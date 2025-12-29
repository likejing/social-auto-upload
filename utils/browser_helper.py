# -*- coding: utf-8 -*-
"""
浏览器助手模块
提供统一的浏览器创建和管理接口，支持Playwright和比特浏览器
"""
import logging
from typing import Optional, Tuple
from playwright.async_api import Browser, BrowserContext, async_playwright, Playwright

from conf import (
    BIT_BROWSER_URL,
    LOCAL_CHROME_PATH,
    LOCAL_CHROME_HEADLESS,
    DEFAULT_BROWSER_TYPE
)
from utils.bitbrowser_connector import BitBrowserConnector, get_browser_manager

logger = logging.getLogger(__name__)


async def create_browser_and_context(
    browser_type: str = None,
    browser_id: str = None,
    account_file: str = None,
    headless: bool = None
) -> Tuple[Browser, BrowserContext]:
    """
    创建浏览器和上下文（统一接口）

    Args:
        browser_type: 浏览器类型 ("playwright" 或 "bitbrowser")，默认使用配置文件中的默认值
        browser_id: 比特浏览器窗口ID (仅bitbrowser模式需要)
        account_file: cookie文件路径
        headless: 是否无头模式，默认使用配置文件中的设置

    Returns:
        (Browser, BrowserContext) 元组

    Raises:
        ValueError: 当参数不正确时
        Exception: 当创建失败时
    """
    # 确定浏览器类型
    if browser_type is None:
        browser_type = DEFAULT_BROWSER_TYPE

    # 确定是否无头模式
    if headless is None:
        headless = LOCAL_CHROME_HEADLESS

    logger.info(f"创建浏览器: type={browser_type}, headless={headless}")

    if browser_type == "bitbrowser":
        # 比特浏览器模式
        if not browser_id:
            raise ValueError("比特浏览器模式需要提供 browser_id 参数")

        connector = BitBrowserConnector(BIT_BROWSER_URL)
        browser, context = await connector.get_or_create_browser(
            browser_id=browser_id,
            headless=headless,
            account_file=account_file
        )

        if not browser or not context:
            raise Exception("无法创建比特浏览器实例")

        return browser, context

    else:
        # Playwright模式
        playwright_instance = await async_playwright().start()

        launch_options = {"headless": headless}
        if LOCAL_CHROME_PATH:
            launch_options["executable_path"] = LOCAL_CHROME_PATH

        browser = await playwright_instance.chromium.launch(**launch_options)

        context_options = {}
        if account_file:
            context_options["storage_state"] = account_file

        context = await browser.new_context(**context_options)

        # 应用反检测脚本
        from utils.base_social_media import set_init_script
        context = await set_init_script(context)

        return browser, context


async def close_browser(browser: Browser, browser_type: str = None, browser_id: str = None, delay: float = 2.0):
    """
    关闭浏览器（统一接口）

    Args:
        browser: Playwright Browser对象
        browser_type: 浏览器类型
        browser_id: 比特浏览器窗口ID (仅bitbrowser模式需要)
        delay: 关闭前等待时间（秒）
    """
    import asyncio

    if browser_type is None:
        browser_type = DEFAULT_BROWSER_TYPE

    await asyncio.sleep(delay)

    if browser_type == "bitbrowser":
        # 比特浏览器需要通过API关闭
        if browser_id:
            connector = BitBrowserConnector(BIT_BROWSER_URL)
            await connector.close_browser(browser_id)
    else:
        # Playwright直接关闭
        await browser.close()


def get_account_browser_config(account_id: int) -> dict:
    """
    从数据库获取账号的浏览器配置

    Args:
        account_id: 账号ID

    Returns:
        包含 browser_type 和 bitbrowser_id 的字典
    """
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent / "db" / "database.db"

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT browser_type, bitbrowser_id
                FROM user_info
                WHERE id = ?
            ''', (account_id,))
            result = cursor.fetchone()

            if result:
                return {
                    "browser_type": result["browser_type"] or DEFAULT_BROWSER_TYPE,
                    "bitbrowser_id": result["bitbrowser_id"]
                }
            else:
                return {
                    "browser_type": DEFAULT_BROWSER_TYPE,
                    "bitbrowser_id": None
                }
    except Exception as e:
        logger.error(f"获取账号浏览器配置失败: {e}")
        return {
            "browser_type": DEFAULT_BROWSER_TYPE,
            "bitbrowser_id": None
        }


async def create_browser_for_account(
    account_id: int,
    account_file: str = None,
    headless: bool = None
) -> Tuple[Browser, BrowserContext, dict]:
    """
    为指定账号创建浏览器（自动从数据库获取配置）

    Args:
        account_id: 账号ID
        account_file: cookie文件路径
        headless: 是否无头模式

    Returns:
        (Browser, BrowserContext, browser_config) 元组
    """
    config = get_account_browser_config(account_id)

    browser, context = await create_browser_and_context(
        browser_type=config["browser_type"],
        browser_id=config["bitbrowser_id"],
        account_file=account_file,
        headless=headless
    )

    return browser, context, config


class BrowserContextManager:
    """
    浏览器上下文管理器，用于with语句自动管理浏览器生命周期
    """

    def __init__(self, browser_type: str = None, browser_id: str = None,
                 account_file: str = None, headless: bool = None):
        self.browser_type = browser_type
        self.browser_id = browser_id
        self.account_file = account_file
        self.headless = headless
        self.browser = None
        self.context = None

    async def __aenter__(self):
        self.browser, self.context = await create_browser_and_context(
            browser_type=self.browser_type,
            browser_id=self.browser_id,
            account_file=self.account_file,
            headless=self.headless
        )
        return self.browser, self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await close_browser(
                self.browser,
                browser_type=self.browser_type,
                browser_id=self.browser_id
            )

# -*- coding: utf-8 -*-
"""
比特浏览器与Playwright连接器模块
提供通过比特浏览器启动Playwright的功能
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import Browser, BrowserContext, async_playwright, Playwright

from utils.bitbrowser_api import BitBrowserAPI, get_bitbrowser_api
from utils.base_social_media import set_init_script

bitbrowser_logger = logging.getLogger(__name__)


class BitBrowserConnector:
    """比特浏览器连接器，用于连接Playwright和比特浏览器"""

    def __init__(self, bit_browser_url: str = "http://127.0.0.1:2000"):
        """
        初始化比特浏览器连接器

        Args:
            bit_browser_url: 比特浏览器Local API地址
        """
        self.api = get_bitbrowser_api(bit_browser_url)
        self.bit_browser_url = bit_browser_url
        self.current_browser_id: Optional[str] = None
        self.current_pids: Optional[Dict[str, int]] = None

    def check_connection(self) -> bool:
        """
        检查与比特浏览器的连接状态

        Returns:
            连接正常返回True，否则返回False
        """
        return self.api.health_check()

    async def open_browser(self, browser_id: str,
                          headless: bool = False,
                          args: list = None) -> Optional[Browser]:
        """
        打开比特浏览器窗口并返回Playwright Browser对象

        Args:
            browser_id: 比特浏览器窗口ID
            headless: 是否无头模式 (注意：比特浏览器推荐有头模式)
            args: 额外的浏览器启动参数

        Returns:
            Playwright Browser对象，失败返回None
        """
        if not self.check_connection():
            bitbrowser_logger.error("无法连接到比特浏览器API")
            return None

        # 构建启动参数
        launch_args = args or []
        if headless:
            launch_args.append("--headless")

        # 打开比特浏览器窗口
        open_result = self.api.open_browser(browser_id, args=launch_args, queue=True)
        if not open_result:
            bitbrowser_logger.error(f"打开浏览器窗口失败: {browser_id}")
            return None

        ws_endpoint = open_result.get("ws")
        if not ws_endpoint:
            bitbrowser_logger.error("未获取到WebSocket连接地址")
            return None

        bitbrowser_logger.info(f"成功打开浏览器窗口: {browser_id}")
        bitbrowser_logger.debug(f"WebSocket地址: {ws_endpoint}")

        # 使用Playwright连接到已打开的浏览器
        playwright_instance = await async_playwright().start()

        try:
            # 连接到比特浏览器的WebSocket端点
            browser = await playwright_instance.chromium.connect_over_cdp(ws_endpoint)
            self.current_browser_id = browser_id
            bitbrowser_logger.info("成功通过Playwright连接到比特浏览器")
            return browser
        except Exception as e:
            bitbrowser_logger.error(f"连接Playwright到比特浏览器失败: {e}")
            # 打开失败，关闭浏览器窗口
            self.api.close_browser(browser_id)
            return None

    async def close_browser(self, browser_id: str = None, delay: float = 5.0) -> bool:
        """
        关闭比特浏览器窗口

        Args:
            browser_id: 浏览器窗口ID，如果为None则使用当前浏览器ID
            delay: 关闭前等待时间（秒），默认5秒

        Returns:
            成功返回True，否则返回False
        """
        target_id = browser_id or self.current_browser_id
        if not target_id:
            bitbrowser_logger.warning("没有指定要关闭的浏览器ID")
            return False

        # 等待进程彻底退出
        await asyncio.sleep(delay)

        result = self.api.close_browser(target_id)
        if result:
            bitbrowser_logger.info(f"成功关闭浏览器窗口: {target_id}")
            if target_id == self.current_browser_id:
                self.current_browser_id = None
        else:
            bitbrowser_logger.error(f"关闭浏览器窗口失败: {target_id}")

        return result

    async def create_context_from_browser(self, browser: Browser,
                                         account_file: str = None,
                                         storage_state: Dict = None) -> BrowserContext:
        """
        从已打开的浏览器创建上下文

        Args:
            browser: Playwright Browser对象
            account_file: cookie文件路径 (可选)
            storage_state: 存储状态字典 (可选)

        Returns:
            BrowserContext对象
        """
        # 创建上下文
        if account_file:
            context = await browser.new_context(storage_state=account_file)
        elif storage_state:
            context = await browser.new_context(storage_state=storage_state)
        else:
            context = await browser.new_context()

        # 应用反检测脚本
        context = await set_init_script(context)

        return context

    async def get_or_create_browser(self, browser_id: str,
                                    headless: bool = False,
                                    account_file: str = None) -> tuple:
        """
        获取或创建浏览器和上下文（便捷方法）

        Args:
            browser_id: 比特浏览器窗口ID
            headless: 是否无头模式
            account_file: cookie文件路径 (可选)

        Returns:
            (Browser, BrowserContext) 元组，失败返回 (None, None)
        """
        browser = await self.open_browser(browser_id, headless=headless)
        if not browser:
            return None, None

        # 对于通过CDP连接的比特浏览器，使用已有的context而不是创建新的
        try:
            # 获取浏览器已有的contexts
            contexts = browser.contexts
            if contexts and len(contexts) > 0:
                # 使用第一个已有的context
                context = contexts[0]
                bitbrowser_logger.info("使用比特浏览器已有的context")

                # 如果需要添加cookies，从文件加载并添加
                if account_file:
                    import json
                    from pathlib import Path
                    cookie_file = Path(account_file)
                    if cookie_file.exists():
                        with open(cookie_file, 'r') as f:
                            storage_state = json.load(f)
                            if 'cookies' in storage_state:
                                await context.add_cookies(storage_state['cookies'])
                                bitbrowser_logger.info("已添加cookies到context")
            else:
                # 如果没有context，创建新的（这种情况较少见）
                context = await self.create_context_from_browser(browser, account_file=account_file)
                bitbrowser_logger.info("创建了新的context")

            return browser, context
        except Exception as e:
            bitbrowser_logger.error(f"获取context失败: {e}，尝试创建新context")
            # 如果获取已有context失败，尝试创建新的
            context = await self.create_context_from_browser(browser, account_file=account_file)
            return browser, context

    def get_browser_info(self, browser_id: str) -> Optional[Dict[str, Any]]:
        """
        获取浏览器窗口信息

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            浏览器信息字典，失败返回None
        """
        return self.api.get_browser_detail(browser_id)

    def list_browsers(self, name: str = None) -> Optional[list]:
        """
        列出所有浏览器窗口

        Args:
            name: 窗口名称过滤 (可选)

        Returns:
            浏览器列表，失败返回None
        """
        return self.api.list_browsers(name=name)

    def is_browser_opened(self, browser_id: str) -> bool:
        """
        检查浏览器是否已打开

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            已打开返回True，否则返回False
        """
        return self.api.is_browser_opened(browser_id)

    async def create_new_browser_window(self, name: str, platform_url: str,
                                       remark: str = None,
                                       proxy_config: Dict = None) -> Optional[str]:
        """
        创建新的浏览器窗口

        Args:
            name: 窗口名称
            platform_url: 平台URL
            remark: 备注 (可选)
            proxy_config: 代理配置 (可选)

        Returns:
            新创建的浏览器ID，失败返回None
        """
        browser_id = self.api.create_browser_for_platform(
            name=name,
            platform_url=platform_url,
            remark=remark,
            proxy_config=proxy_config
        )
        if browser_id:
            bitbrowser_logger.info(f"成功创建浏览器窗口: {browser_id}")
        else:
            bitbrowser_logger.error("创建浏览器窗口失败")
        return browser_id


class BrowserManager:
    """
    浏览器管理器，统一管理Playwright和比特浏览器的创建
    """

    def __init__(self, browser_type: str = "playwright",
                 bitbrowser_url: str = "http://127.0.0.1:2000",
                 local_chrome_path: str = None,
                 headless: bool = False):
        """
        初始化浏览器管理器

        Args:
            browser_type: 浏览器类型 ("playwright" 或 "bitbrowser")
            bitbrowser_url: 比特浏览器API地址
            local_chrome_path: 本地Chrome路径 (仅playwright模式)
            headless: 是否无头模式
        """
        self.browser_type = browser_type.lower()
        self.bitbrowser_url = bitbrowser_url
        self.local_chrome_path = local_chrome_path
        self.headless = headless

        if self.browser_type == "bitbrowser":
            self.connector = BitBrowserConnector(bitbrowser_url)
        else:
            self.connector = None

    async def create_browser(self, browser_id: str = None,
                            account_file: str = None) -> tuple:
        """
        创建浏览器和上下文

        Args:
            browser_id: 比特浏览器窗口ID (仅bitbrowser模式需要)
            account_file: cookie文件路径 (可选)

        Returns:
            (Browser, BrowserContext) 元组，失败返回 (None, None)
        """
        if self.browser_type == "bitbrowser":
            if not browser_id:
                bitbrowser_logger.error("比特浏览器模式需要提供browser_id")
                return None, None
            return await self.connector.get_or_create_browser(
                browser_id=browser_id,
                headless=self.headless,
                account_file=account_file
            )
        else:
            # Playwright模式
            playwright_instance = await async_playwright().start()
            launch_options = {"headless": self.headless}
            if self.local_chrome_path:
                launch_options["executable_path"] = self.local_chrome_path

            browser = await playwright_instance.chromium.launch(**launch_options)
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            return browser, context

    async def close_browser(self, browser, browser_id: str = None):
        """
        关闭浏览器

        Args:
            browser: Playwright Browser对象
            browser_id: 比特浏览器窗口ID (仅bitbrowser模式需要)
        """
        if self.browser_type == "bitbrowser":
            await self.connector.close_browser(browser_id or self.current_browser_id)
        else:
            await browser.close()


# 全局浏览器管理器实例
_browser_manager = None


def get_browser_manager(browser_type: str = "playwright",
                       bitbrowser_url: str = "http://127.0.0.1:2000",
                       local_chrome_path: str = None,
                       headless: bool = False) -> BrowserManager:
    """
    获取浏览器管理器实例（单例模式）

    Args:
        browser_type: 浏览器类型
        bitbrowser_url: 比特浏览器API地址
        local_chrome_path: 本地Chrome路径
        headless: 是否无头模式

    Returns:
        BrowserManager实例
    """
    global _browser_manager
    _browser_manager = BrowserManager(
        browser_type=browser_type,
        bitbrowser_url=bitbrowser_url,
        local_chrome_path=local_chrome_path,
        headless=headless
    )
    return _browser_manager

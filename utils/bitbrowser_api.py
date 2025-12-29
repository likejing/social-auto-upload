# -*- coding: utf-8 -*-
"""
比特浏览器API集成模块
提供与比特浏览器Local API的交互功能
"""
import requests
import json
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin

bitbrowser_logger = logging.getLogger(__name__)


class BitBrowserAPI:
    """比特浏览器API客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:2000"):
        """
        初始化比特浏览器API客户端

        Args:
            base_url: 比特浏览器Local API地址，默认为 http://127.0.0.1:2000
        """
        self.base_url = base_url.rstrip('/')
        bitbrowser_logger.info(f"初始化比特浏览器API: {base_url}")

    def _request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送POST请求到比特浏览器API

        Args:
            endpoint: API端点路径
            data: 请求数据

        Returns:
            响应数据
        """
        url = urljoin(self.base_url, endpoint)
        headers = {'Content-Type': 'application/json'}

        try:
            bitbrowser_logger.debug(f"发送请求到: {url}, 数据: {data}")
            response = requests.post(url, headers=headers, json=data or {}, timeout=30)
            response.raise_for_status()
            result = response.json()
            bitbrowser_logger.debug(f"响应数据: {result}")
            return result
        except requests.exceptions.RequestException as e:
            bitbrowser_logger.error(f"请求失败: {e}")
            return {"success": False, "msg": str(e)}

    def health_check(self) -> bool:
        """
        健康检查，测试连接是否成功

        Returns:
            连接成功返回True，否则返回False
        """
        result = self._request("/health")
        return result.get("success", False)

    def create_browser(self, browser_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建浏览器窗口

        Args:
            browser_config: 浏览器配置，包含:
                - name: 窗口名称
                - platform: 平台URL (可选)
                - remark: 备注 (可选)
                - browserFingerPrint: 指纹对象 (必填)

        Returns:
            创建结果，包含浏览器ID等信息
        """
        # 默认指纹配置
        default_fingerprint = {
            "coreVersion": "130",
            "ostype": "PC",
            "os": "Win32",
            "osVersion": "11,10"
        }

        if "browserFingerPrint" not in browser_config:
            browser_config["browserFingerPrint"] = default_fingerprint

        return self._request("/browser/update", browser_config)

    def open_browser(self, browser_id: str, args: List[str] = None,
                     queue: bool = True, new_page_url: str = None) -> Optional[Dict[str, Any]]:
        """
        打开浏览器窗口

        Args:
            browser_id: 浏览器窗口ID
            args: 浏览器启动参数 (可选)
            queue: 是否队列方式打开 (默认True)
            new_page_url: 打开时指定的URL (可选)

        Returns:
            包含ws、http连接地址等信息，失败返回None
        """
        data = {
            "id": browser_id,
            "args": args or [],
            "queue": queue
        }
        if new_page_url:
            data["newPageUrl"] = new_page_url

        result = self._request("/browser/open", data)
        if result.get("success"):
            return result.get("data")
        return None

    def close_browser(self, browser_id: str) -> bool:
        """
        关闭浏览器窗口

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            成功返回True，否则返回False
        """
        result = self._request("/browser/close", {"id": browser_id})
        return result.get("success", False)

    def delete_browser(self, browser_id: str) -> bool:
        """
        删除浏览器窗口

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            成功返回True，否则返回False
        """
        result = self._request("/browser/delete", {"id": browser_id})
        return result.get("success", False)

    def get_browser_detail(self, browser_id: str) -> Optional[Dict[str, Any]]:
        """
        获取浏览器窗口详情

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            浏览器详情，失败返回None
        """
        result = self._request("/browser/detail", {"id": browser_id})
        if result.get("success"):
            return result.get("data")
        return None

    def list_browsers(self, page: int = 0, page_size: int = 100,
                      group_id: str = None, name: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        获取浏览器窗口列表

        Args:
            page: 页码，从0开始
            page_size: 每页数量，最大100
            group_id: 分组ID (可选)
            name: 窗口名称模糊匹配 (可选)

        Returns:
            浏览器列表，失败返回None
        """
        data = {
            "page": page,
            "pageSize": min(page_size, 100)
        }
        if group_id:
            data["groupId"] = group_id
        if name:
            data["name"] = name

        result = self._request("/browser/list", data)
        if result.get("success"):
            return result.get("data", {}).get("list", [])
        return None

    def get_browser_pids(self, browser_ids: List[str]) -> Dict[str, int]:
        """
        获取浏览器窗口的进程ID

        Args:
            browser_ids: 浏览器窗口ID列表

        Returns:
            浏览器ID到进程ID的映射
        """
        result = self._request("/browser/pids", {"ids": browser_ids})
        if result.get("success"):
            return result.get("data", {})
        return {}

    def is_browser_opened(self, browser_id: str) -> bool:
        """
        检查浏览器窗口是否已打开

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            已打开返回True，否则返回False
        """
        pids = self.get_browser_pids([browser_id])
        return browser_id in pids and pids[browser_id] > 0

    def update_browser_proxy(self, browser_ids: List[str],
                            proxy_type: str, host: str, port: int,
                            proxy_username: str = None, proxy_password: str = None,
                            proxy_method: int = 2) -> bool:
        """
        批量修改窗口代理信息

        Args:
            browser_ids: 窗口ID列表
            proxy_type: 代理类型 (http, https, socks5, ssh)
            host: 代理主机
            port: 代理端口
            proxy_username: 代理用户名 (可选)
            proxy_password: 代理密码 (可选)
            proxy_method: 代理方式 (2=自定义, 3=提取IP)

        Returns:
            成功返回True，否则返回False
        """
        data = {
            "ids": browser_ids,
            "proxyMethod": proxy_method,
            "proxyType": proxy_type,
            "host": host,
            "port": port
        }
        if proxy_username:
            data["proxyUserName"] = proxy_username
        if proxy_password:
            data["proxyPassword"] = proxy_password

        result = self._request("/browser/proxy/update", data)
        return result.get("success", False)

    def reset_browser_status(self, browser_id: str) -> bool:
        """
        重置浏览器关闭状态
        用于窗口异常关闭后，状态显示为"打开中/关闭中"时重置

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            成功返回True，否则返回False
        """
        result = self._request("/browser/closing/reset", {"id": browser_id})
        return result.get("success", False)

    def get_cookies(self, browser_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取已打开窗口的实时cookies

        Args:
            browser_id: 浏览器窗口ID

        Returns:
            cookies列表，失败返回None
        """
        result = self._request("/browser/cookies/get", {"browserId": browser_id})
        if result.get("success"):
            return result.get("data")
        return None

    def set_cookies(self, browser_id: str, cookies: List[Dict[str, Any]]) -> bool:
        """
        对已打开窗口设置实时cookie

        Args:
            browser_id: 浏览器窗口ID
            cookies: cookies列表

        Returns:
            成功返回True，否则返回False
        """
        result = self._request("/browser/cookies/set", {
            "browserId": browser_id,
            "cookies": cookies
        })
        return result.get("success", False)

    def clear_cookies(self, browser_id: str, save_synced: bool = True) -> bool:
        """
        清空cookie

        Args:
            browser_id: 浏览器窗口ID
            save_synced: 是否清空已同步到服务端的cookie (默认True)

        Returns:
            成功返回True，否则返回False
        """
        result = self._request("/browser/cookies/clear", {
            "browserId": browser_id,
            "saveSynced": save_synced
        })
        return result.get("success", False)

    def create_browser_for_platform(self, name: str, platform_url: str,
                                    remark: str = None, proxy_config: Dict = None) -> Optional[str]:
        """
        为指定平台创建浏览器窗口的便捷方法

        Args:
            name: 窗口名称
            platform_url: 平台URL
            remark: 备注 (可选)
            proxy_config: 代理配置 (可选)

        Returns:
            创建的浏览器ID，失败返回None
        """
        browser_config = {
            "name": name,
            "platform": platform_url,
            "browserFingerPrint": {
                "coreVersion": "130",
                "ostype": "PC",
                "os": "Win32",
                "osVersion": "11,10"
            }
        }

        if remark:
            browser_config["remark"] = remark

        if proxy_config:
            browser_config.update({
                "proxyMethod": 2,
                "proxyType": proxy_config.get("type", "socks5"),
                "host": proxy_config.get("host"),
                "port": proxy_config.get("port")
            })
            if "username" in proxy_config:
                browser_config["proxyUserName"] = proxy_config["username"]
            if "password" in proxy_config:
                browser_config["proxyPassword"] = proxy_config["password"]

        result = self.create_browser(browser_config)
        if result.get("success"):
            return result.get("data", {}).get("id")
        return None


# 默认API实例
_default_api = None


def get_bitbrowser_api(base_url: str = "http://127.0.0.1:2000") -> BitBrowserAPI:
    """
    获取比特浏览器API实例（单例模式）

    Args:
        base_url: 比特浏览器Local API地址

    Returns:
        BitBrowserAPI实例
    """
    global _default_api
    if _default_api is None:
        _default_api = BitBrowserAPI(base_url)
    return _default_api

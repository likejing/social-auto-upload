from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"
LOCAL_CHROME_PATH = ""   # change me necessary！ for example C:/Program Files/Google/Chrome/Application/chrome.exe
LOCAL_CHROME_HEADLESS = False


# 比特浏览器配置
BIT_BROWSER_URL = "http://127.0.0.1:54345"  # 比特浏览器Local API地址
# 默认浏览器类型: "playwright" 或 "bitbrowser"
# - playwright: 使用原生的Playwright浏览器
# - bitbrowser: 使用比特浏览器
DEFAULT_BROWSER_TYPE = "playwright"

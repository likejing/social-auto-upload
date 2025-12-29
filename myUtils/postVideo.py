import asyncio
import sqlite3
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


def get_account_browser_config_by_filepath(file_path):
    """从数据库获取账号的浏览器配置（通过文件路径）"""
    db_path = Path(BASE_DIR / "db" / "database.db")

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT browser_type, bitbrowser_id
                FROM user_info
                WHERE filePath = ?
            ''', (file_path,))
            result = cursor.fetchone()

            if result:
                return {
                    "browser_type": result["browser_type"] or "playwright",
                    "bitbrowser_id": result["bitbrowser_id"]
                }
            else:
                return {
                    "browser_type": "playwright",
                    "bitbrowser_id": None
                }
    except Exception as e:
        print(f"获取账号浏览器配置失败: {e}")
        return {
            "browser_type": "playwright",
            "bitbrowser_id": None
        }


def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0, is_draft=False):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")

            # 获取浏览器配置（从cookie文件名反向查找数据库）
            cookie_filename = cookie.name
            browser_config = get_account_browser_config_by_filepath(cookie_filename)

            app = TencentVideo(
                title, str(file), tags, publish_datetimes[index], cookie, category, is_draft,
                browser_type=browser_config["browser_type"],
                bitbrowser_id=browser_config["bitbrowser_id"]
            )
            asyncio.run(app.main(), debug=False)


def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0,
                      thumbnail_path = '',
                      productLink = '', productTitle = ''):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")

            # 获取浏览器配置（从cookie文件名反向查找数据库）
            # cookie是Path对象，需要获取文件名
            cookie_filename = cookie.name
            browser_config = get_account_browser_config_by_filepath(cookie_filename)

            app = DouYinVideo(
                title, str(file), tags, publish_datetimes[index], cookie,
                thumbnail_path, productLink, productTitle,
                browser_type=browser_config["browser_type"],
                bitbrowser_id=browser_config["bitbrowser_id"]
            )
            asyncio.run(app.main(), debug=False)


def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")

            # 获取浏览器配置（从cookie文件名反向查找数据库）
            cookie_filename = cookie.name
            browser_config = get_account_browser_config_by_filepath(cookie_filename)

            app = KSVideo(
                title, str(file), tags, publish_datetimes[index], cookie,
                browser_type=browser_config["browser_type"],
                bitbrowser_id=browser_config["bitbrowser_id"]
            )
            asyncio.run(app.main(), debug=False)

def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    file_num = len(files)
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = 0
    for index, file in enumerate(files):
        for cookie in account_file:
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")

            # 获取浏览器配置（从cookie文件名反向查找数据库）
            cookie_filename = cookie.name
            browser_config = get_account_browser_config_by_filepath(cookie_filename)

            app = XiaoHongShuVideo(
                title, file, tags, publish_datetimes, cookie,
                browser_type=browser_config["browser_type"],
                bitbrowser_id=browser_config["bitbrowser_id"]
            )
            asyncio.run(app.main(), debug=False)



# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")
import asyncio
import json
import re
import time
from pathlib import Path
from typing import List, Optional, Union

import httpx
import qrcode
from bs4 import BeautifulSoup
from loguru import logger

import WeiboBot.const as const
from WeiboBot.exception import (
    CommentError,
    DeleteCommentError,
    DeleteWeiboError,
    LikeWeiboError,
    PostWeiboError,
    RepostWeiboError,
    SendMessageError,
    UploadPicError,
    WeiboNotExist,
)
from WeiboBot.model import Chat, ChatDetail, Comment, Page, User, Weibo
from WeiboBot.typing import CID, MID
from WeiboBot.util import (
    get_cookies_value,
    httpx_cookies_to_playwright,
    load_cookies,
    save_cookies,
)


class NetTool:
    def __init__(
        self, cookies: Union[str, dict, Path] = Path("weibobot_cookies.json")
    ) -> None:
        """初始化网络工具类。

        Args:
            cookies (str): 微博的cookies字符串
        """
        super(NetTool, self).__init__()
        self.client = httpx.AsyncClient(max_redirects=10)
        self.mid: int = 0
        self._last_refresh_token_time = 0
        self._token_refresh_interval = 60 * 10  # 10分钟
        self.cookies_path = cookies
        if isinstance(cookies, str):
            logger.info("从字符串加载cookies")
            cookies_dict = json.loads(cookies)
            for name, value in cookies_dict.items():
                self.client.cookies.set(name, value)
        elif isinstance(cookies, dict):
            logger.info("从字典加载cookies")
            for name, value in cookies.items():
                self.client.cookies.set(name, value)
        elif isinstance(cookies, Path):
            logger.info("从文件加载cookies")
            if not load_cookies(cookies, self.client):
                logger.info("文件不存在，将使用扫码登录")

    async def __aenter__(self):
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _refresh_token(self):
        response = await self.client.get(
            "https://m.weibo.cn/api/config", headers={"Referer": "https://m.weibo.cn/"}
        )
        response.raise_for_status()
        for cookie in response.cookies.jar:
            logger.debug(
                f"Cookie: {cookie.name}={cookie.value} "
                f"Domain={cookie.domain} "
                f"Path={cookie.path} "
                f"Expires={cookie.expires}"
            )
            # 直接设置到 client 的 cookies 中
            self.client.cookies.set(
                cookie.name, cookie.value, domain=cookie.domain, path=cookie.path
            )

        # 原有的 token 处理
        result = response.json()
        if result["data"]["login"]:
            token = result["data"]["st"]
            self.client.cookies.set("XSRF-TOKEN", token, domain="m.weibo.cn")
            save_cookies(self.cookies_path, self.client)

    async def get_token(self) -> str:
        now = time.time()
        if now - self._last_refresh_token_time > self._token_refresh_interval:
            await self._refresh_token()
            self._last_refresh_token_time = now
        return get_cookies_value(self.client, "XSRF-TOKEN")

    async def login(self) -> int:
        """登录微博。"""
        if not self.client.cookies:
            await self.login_by_qr_code()
            return await self.check_login_status()
        else:
            return await self.check_login_status()

    async def get_qrcode_url(self) -> str:
        params = {
            "entry": "wapsso",
            "size": "180",
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
        }
        response = await self.client.get(
            "https://passport.weibo.com/sso/v2/qrcode/image",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        qrid = result["data"]["qrid"]
        qrcode_url = f"https://passport.weibo.cn/signin/qrcode/scan?qr={qrid}"
        qrcode_file = "qrcode.png"
        logger.info(f"二维码URL: {qrcode_url}")
        logger.info(
            f"请使用微博扫描二维码登录，如果显示不全，可以打开根目录下的{qrcode_file}文件"
        )
        qr = qrcode.QRCode()
        qr.add_data(qrcode_url)
        qr.make(fit=True)
        qr.print_ascii()
        qr.make_image(fill_color="black", back_color="white").save(qrcode_file)
        return qrid

    async def login_by_qr_code(self):
        qrid = await self.get_qrcode_url()
        while True:
            await asyncio.sleep(1)
            params = {
                "entry": "wapsso",
                "source": "wapsso",
                "url": "https://m.weibo.cn/",
                "qrid": qrid,
            }
            headers = {
                "Referer": "https://m.weibo.cn/",
            }
            response = await self.client.get(
                "https://passport.weibo.com/sso/v2/qrcode/check",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()
            retcode = result["retcode"]
            if retcode == 50114001:
                logger.debug("二维码未使用")
                continue
            elif retcode == 50114003:
                logger.info("二维码已过期")
                qrid = await self.get_qrcode_url()
            elif retcode == 50114002:
                logger.info("成功扫描，请在手机点击确认以登录")
            else:
                logger.info("二维码已使用")
                logger.info(result)
                alt = result.get("data", {}).get("url")
                logger.info(f"跳转 URL: {alt}")
                # 访问跳转链接，完成登录
                headers = {
                    "Referer": "https://m.weibo.cn/",
                }
                final_response = await self.client.get(
                    alt, follow_redirects=True, headers=headers
                )
                final_response.raise_for_status()
                save_cookies(self.cookies_path, self.client)
                # 此时，client.cookies 中包含了登录后的 Cookies
                return

    async def check_login_status(self) -> int:
        logger.info("检查登录状态……")
        url = "https://m.weibo.cn/api/config"
        headers = {
            "Referer": "https://m.weibo.cn/",
        }
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        isLogin = data["data"]["login"]
        if not isLogin:
            logger.warning("未登录")
            return 0
        token = data["data"]["st"]
        self.client.cookies.set("XSRF-TOKEN", token)
        self._last_refresh_token_time = time.time()
        self.mid = int(data["data"]["uid"])
        logger.info(f"登录成功，用户ID: {self.mid}")
        return self.mid

    async def user_info(self, user_id: MID) -> User:
        """获取用户信息。

        Args:
            user_id (int): 用户ID

        Returns:
            User: 用户信息
        """
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        params = {
            "uid": int(user_id),
        }
        response = await self.client.get(
            "https://m.weibo.cn/profile/info", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        user = User.model_validate(result["data"]["user"])
        user.statuses = [
            Weibo.model_validate(weibo) for weibo in result["data"]["statuses"]
        ]
        return user

    async def post_weibo(self, content: str, visible: const.VISIBLE) -> Optional[Weibo]:
        """发布微博。

        Args:
            content (str): 微博内容
            visible (const.VISIBLE): 可见性设置

        Returns:
            Dict[str, Any]: 发布结果
        """
        params = {
            "content": content,
            "visible": visible.value,
            "st": await self.get_token(),
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/statuses/update", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()

        if result["ok"] == 1:
            weibo = Weibo.model_validate(result["data"])
            return weibo
        else:
            raise PostWeiboError(result["msg"])

    async def repost_weibo(
        self, mid: MID, content: str, dualPost: bool = False
    ) -> Weibo:
        """转发微博。

        Args:
            mid (Union[str, int]): 微博ID
            content (str): 转发内容
            dualPost (bool): 是否同时评论

        Returns:
            Weibo: 转发结果
        """
        params = {
            "id": mid,
            "content": content,
            "mid": mid,
            "st": await self.get_token(),
            "dualPost": int(dualPost),
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/statuses/repost",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            weibo = Weibo.model_validate(result["data"])
            return weibo
        else:
            raise RepostWeiboError(result["msg"])

    async def weibo_info(self, mid: MID, comments_count: int = 0) -> Weibo:
        """获取微博详细信息。

        Args:
            mid (Union[str, int]): 微博ID

        Returns:
            Weibo: 微博信息
        """
        url = f"https://m.weibo.cn/detail/{mid}"
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        r = response.text

        soup = BeautifulSoup(r, "html.parser")
        error_msg = soup.select_one("body > div > p")
        if error_msg and error_msg.get_text().strip() == "微博不存在或暂无查看权限!":
            raise WeiboNotExist(f"微博不存在或暂无查看权限! {mid}")

        result = json.loads(
            re.findall(r"(?<=render_data = \[)[\s\S]*(?=\]\[0\])", r)[0]
        )["status"]
        weibo = Weibo.model_validate(result)
        weibo.comments = await self.get_weibo_comments(mid, comments_count)
        return weibo

    async def get_weibo_comments(self, mid: MID, count: int = 20) -> List[Comment]:
        """获取微博评论。
        Args:
            mid (Union[str, int]): 微博ID
            count (int): 获取评论数量，默认20条，-1表示获取所有评论
        Returns:
            List[Comment]: 评论列表
        """
        comments = []
        max_id = 0
        if count == 0:
            return []
        while True:
            url = "https://m.weibo.cn/comments/hotflow"
            headers = {
                "Referer": "https://m.weibo.cn/",
                "x-xsrf-token": await self.get_token(),
            }
            params = {
                "id": mid,
                "mid": mid,
                "max_id": max_id,
                "max_id_type": 0,
            }

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            if not comments:  # 第一次请求
                total = result["data"]["total_number"]
                if count != -1:
                    count = min(count, total)

            new_comments = [
                Comment.model_validate(data)
                for data in result["data"]["data"]
                if data["id"] not in [c.id for c in comments]
            ]
            comments.extend(new_comments)

            max_id = result["data"]["max_id"]
            if max_id == 0 or (count != -1 and len(comments) >= count):
                break

        return comments if count == -1 else comments[:count]

    async def upload_chat_file(self, tuid: MID, file: Path) -> str:
        """上传聊天文件。

        Args:
            tuid (int): 接收者用户ID
            file (Path): 文件路径

        Returns:
            str: 文件ID
        """
        files = {"file": (file.name, open(file, "rb"), "image/jpeg")}
        data = {"tuid": tuid, "st": await self.get_token()}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/chat/upload",
            headers=headers,
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()
        if "fids" not in result.get("data", {}):
            raise UploadPicError()
        return result["data"]["fids"]

    async def upload_comment_pic(self, file: Path) -> str:
        """上传评论图片。

        Args:
            file (Path): 图片文件路径

        Returns:
            str: 图片ID
        """
        files = {"pic": (file.name, open(file, "rb"), "image/jpeg")}
        data = {"type": "json", "st": await self.get_token()}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/statuses/uploadPic",
            headers=headers,
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()
        if "pic_id" not in result:
            raise UploadPicError()
        return result["pic_id"]

    async def send_message(
        self, uid: MID, content: str, file: Optional[Path] = None
    ) -> ChatDetail:
        """发送私信。

        Args:
            uid (Union[str, int]): 接收者用户ID
            content (str): 消息内容
            file (Path): 附件文件路径

        Returns:
            ChatDetail: 发送结果
        """
        params = {
            "uid": int(uid),
            "content": content,
            "st": await self.get_token(),
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        if file and file.exists():
            media_type = const.MEDIA.PHOTO.value
            fids = await self.upload_chat_file(tuid=uid, file=file)
            params["media_type"] = media_type
            params["content"] = ""
            params["fids"] = fids

        response = await self.client.post(
            "https://m.weibo.cn/api/chat/send", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            chat_detail = ChatDetail.model_validate(result["data"])
            return chat_detail
        else:
            raise SendMessageError(result["msg"])

    async def user_chat(
        self, uid: MID, since_id: int = 0, is_continuous=0
    ) -> ChatDetail:
        """获取与指定用户的聊天记录。

        Args:
            uid (Union[str, int]): 用户ID
            since_id (int): 起始消息ID

        Returns:
            ChatDetail: 聊天记录
        """
        params = {
            "count": 20,
            "uid": int(uid),
            "since_id": since_id,
            "is_continuous": is_continuous,
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.get(
            "https://m.weibo.cn/api/chat/list", params=params, headers=headers
        )
        response.raise_for_status()

        data = response.json()
        return ChatDetail.model_validate(data["data"])

    async def chat_list(self, page: int = 1) -> List[Chat]:
        """获取聊天列表。

        Args:
            page (int): 页码

        Returns:
            List[Chat]: 聊天列表
        """
        params = {"page": page}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.get(
            "https://m.weibo.cn/message/msglist", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        chat_list = [Chat.model_validate(chat) for chat in result["data"]]
        return chat_list

    async def mentions_cmt(self, page: int = 1) -> List[Comment]:
        """获取@我的评论。

        Args:
            page (int): 页码

        Returns:
            List[Comment]: @我的评论列表
        """
        params = {"page": page}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.get(
            "https://m.weibo.cn/message/mentionsCmt", params=params, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        cmt_list = [Comment.model_validate(cmt) for cmt in data["data"]]
        return cmt_list

    async def refresh_page(self, max_id: int = 0) -> Page:
        """刷新关注页面。

        Args:
            max_id (Union[str, int]): 最大ID

        Returns:
            Page: 关注页面，注意里面的statuses不是完整微博，需要用weibo_info获取
        """
        params = {"max_id": max_id}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.get(
            "https://m.weibo.cn/feed/friends", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        page = Page.model_validate(result["data"])
        return page

    async def like_weibo(self, mid: MID) -> bool:
        """点赞微博。

        Args:
            mid (Union[str, int]): 微博ID

        Returns:
            bool: 点赞结果
        """
        params = {
            "id": mid,
            "attitude": "heart",
            "st": await self.get_token(),
        }
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/attitudes/create", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            return True
        else:
            raise LikeWeiboError(result["msg"])

    async def del_weibo(self, mid: MID) -> bool:
        """删除微博。

        Args:
            mid (Union[str, int]): 微博ID

        Returns:
            bool: 删除结果
        """
        params = {"mid": mid, "st": await self.get_token()}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/profile/delMyblog", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            return True
        else:
            raise DeleteWeiboError(result["msg"])

    async def comment_weibo(
        self, mid: MID, content: str, file: Optional[Path] = None
    ) -> Comment:
        """评论微博。

        Args:
            mid (Union[str, int]): 微博ID
            content (str): 评论内容
            file (Path, optional): 图片文件路径. 默认为空.

        Returns:
            Comment: 评论结果
        """
        params = {
            "id": mid,
            "mid": mid,
            "content": content,
            "st": await self.get_token(),
        }

        if file and file.exists():
            pic_id = await self.upload_comment_pic(file=file)
            params["picId"] = pic_id
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/api/comments/create", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            comment = Comment.model_validate(result["data"])
            return comment
        else:
            raise CommentError(result["msg"])

    async def del_comment(self, cid: CID) -> bool:
        """删除评论。

        Args:
            cid (Union[str, int]): 评论ID

        Returns:
            bool: 删除结果
        """
        params = {"cid": int(cid), "st": await self.get_token()}
        headers = {
            "Referer": "https://m.weibo.cn/",
            "x-xsrf-token": await self.get_token(),
        }
        response = await self.client.post(
            "https://m.weibo.cn/comments/destroy", params=params, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        if result["ok"] == 1:
            return True
        else:
            raise DeleteCommentError(result["msg"])

    @staticmethod
    async def _ensure_browser_installed():
        try:
            import subprocess

            subprocess.run(
                ["playwright", "install", "chromium"], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"安装 Chromium 失败: {e.stderr.decode()}")

    async def screenshot_weibo(self, url: str) -> bytes:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("请安装playwright")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as e:
                if "Executable doesn't exist" in str(
                    e
                ) or "Chromium revision is not downloaded" in str(e):
                    await self._ensure_browser_installed()
                    browser = await p.chromium.launch(headless=True)
                else:
                    raise
            # iPhone 15
            iphone_15 = p.devices["iPhone 15"]
            context = await browser.new_context(
                **iphone_15,
            )
            # 1. 转换 httpx cookies
            cookies = httpx_cookies_to_playwright(self.client.cookies.jar)
            # 2. 设置 cookies
            if cookies:
                await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            # 移除 #app > div.lite-page-wrap > div > div.lite-page-editor > div
            await page.evaluate(
                """
                const element1 = document.querySelector('#app > div.lite-page-wrap > div > div.main > div > div.wrap');
                if (element1) {
                    element1.remove();
                };
                const element2 = document.querySelector('#app > div.lite-page-wrap > div > div.lite-page-editor');
                if (element2) {
                    element2.remove();
                };

                """
            )

            element = page.locator(
                "#app > div.lite-page-wrap > div > div.main > div.card"
            )
            img = await element.screenshot()
            await browser.close()
            return img

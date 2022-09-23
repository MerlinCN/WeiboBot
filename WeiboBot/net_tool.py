import asyncio
import json
import re
from typing import Dict, Tuple, Union

import requests
import requests.utils

from .const import *
from .exception import *
from .util import *


class NetTool:
    def __init__(self, username: str = "", password: str = "", cookies: str = ""):
        super(NetTool, self).__init__()
        # 暂不支持用户名和密码登录 v1.0
        if username and password:
            raise NotImplementedError("暂不支持用户名和密码登录")
        elif cookies:
            # 如果有cookies则直接使用cookies登录
            pass
        else:
            raise LoginError("登录失败!请输入cookies")

        self.cookies: str = cookies
        self.header: Dict[str, str] = main_header(bytes(self.cookies, encoding="utf-8"))
        self.mainSession: requests.session = requests.session()

        self.cookies_dict = parse_cookies(cookies)

        self.st_times = 0  # 获取st的次数
        self.logger = get_logger(__name__)

    def add_ref(self, value: str) -> Dict[str, str]:
        self.header["referer"] = value
        return self.header

    async def get(self, url: str, params: Dict = None, header=None) -> Dict:
        if header is None:
            header = self.header
        r = self.mainSession.get(url, headers=header, params=params)
        if r.status_code != 200:
            raise RequestError(f"网络错误!状态码:{r.status_code}\n{r.text}")
        self.refresh_cookies()
        result = r.json()
        return result

    async def post(self, url: str, params: Dict = None, header=None, files=None) -> Dict:
        if header is None:
            header = self.header
        r = self.mainSession.post(url, headers=header, data=params, files=files)
        if r.status_code != 200:
            raise RequestError(f"网络错误!状态码:{r.status_code}\n{r.text}")
        self.refresh_cookies()
        result = r.json()
        return result

    def refresh_cookies(self):
        cookies: dict = requests.utils.dict_from_cookiejar(self.mainSession.cookies)
        for k, v in cookies.items():
            for c in self.cookies_dict:
                if c["name"] == k:
                    c["value"] = v

    async def login(self) -> Tuple[bool, int]:
        url = "https://m.weibo.cn/api/config"
        self.add_ref(url)
        data = await self.get(url)
        isLogin = data['data']['login']
        if not isLogin:
            return False, 0
        st = data["data"]["st"]
        self.header["x-xsrf-token"] = st
        roleid = int(data['data']['uid'])
        return True, roleid

    async def st(self):
        """
        获得session token

        :return: session token
        """
        try:
            data = await self.get("https://m.weibo.cn/api/config")
        except Exception:
            if self.st_times > 5:
                self.logger.error("获取st失败!")
                st = self.header["x-xsrf-token"]
                return st
            self.st_times += 1
            return await self.st()
        islogin = data["data"]["login"]
        if islogin is False:
            raise LoginError("登录失败!请输入cookies")
        st = data["data"]["st"]
        return st

    async def user_info(self, user_id: int):
        url = f"https://m.weibo.cn/profile/info?uid={user_id}"
        self.add_ref(f"https://m.weibo.cn/profile/{user_id}")
        return await self.get(url)

    async def post_weibo(self, content: str, visible: VISIBLE):
        params = {
            "content": content,
            "visible": visible.value,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }

        return await self.post("https://m.weibo.cn/api/statuses/update", params=params)

    async def repost_weibo(self, mid: Union[str, int], content: str, dualPost: bool):
        self.add_ref(f"https://m.weibo.cn/compose/repost?id={mid}")
        self.header["x-xsrf-token"] = await self.st()
        data = {
            "id": mid,
            "content": content,
            "mid": mid,
            "st": self.header["x-xsrf-token"],
            "_spr": "screen:2560x1440",
            "dualPost": int(dualPost)
        }
        return await self.post("https://m.weibo.cn/api/statuses/repost", params=data)

    async def weibo_info(self, mid: Union[str, int]) -> dict:
        url = f"https://m.weibo.cn/detail/{mid}"
        r = self.mainSession.get(url, headers=self.header)
        weibo_info = {}
        try:
            weibo_info = json.loads(re.findall(r'(?<=render_data = \[)[\s\S]*(?=\]\[0\])', r.text)[0])[
                "status"]
        except IndexError:
            self.logger.error(f"{url} 解析错误 \n{r.text}")
            raise RequestError("解析微博信息错误")

        return weibo_info

    async def upload_chat_file(self, tuid, file_path):
        files = {
            "file": (file_path, open(file_path, 'rb'), 'image/jpeg')
        }
        params = {
            "tuid": tuid,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        result = await self.post("https://m.weibo.cn/api/chat/upload", params=params, files=files)
        if result['ok'] != 1:
            raise UploadError(f"上传文件错误 {result}")

        return result['data']['fids']

    async def send_message(self, uid: Union[str, int], content: str, file_path: str):

        params = {
            "uid": int(uid),
            "content": content,
            "st": await self.st(),
            "_spr": "screen:2560x1440",
        }

        if file_path:
            media_type = MEDIA.PHOTO.value
            try:
                fids = await self.upload_chat_file(tuid=int(uid), file_path=file_path)
            except RequestError as e:
                self.logger.error(f"文件上传失败 {e}")
                return {}
            params["media_type"] = media_type
            params["content"] = ""
            params["fids"] = fids

        return await self.post("https://m.weibo.cn/api/chat/send", params=params)

    async def user_chat(self, uid: Union[str, int], since_id: int):
        params = {"count": 20, "uid": uid, "since_id": since_id}
        return await self.get("https://m.weibo.cn/api/chat/list", params=params)

    async def chat_list(self, page: int):
        params = {"page": page}
        return await self.get("https://m.weibo.cn/message/msglist", params=params)

    async def mentions_cmt(self, page: int):
        params = {"page": page}
        return await self.get("https://m.weibo.cn/message/mentionsCmt", params=params)

    async def refresh_page(self, max_id: Union[str, int]):
        self.add_ref("https://m.weibo.cn/")
        params = {"max_id": max_id}
        return await self.get("https://m.weibo.cn/feed/friends", params=params)

    async def like(self, mid):
        self.add_ref("https://m.weibo.cn/")
        params = {
            "id": mid,
            "attitude": "heart",
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        return await self.post("https://m.weibo.cn/api/attitudes/create", params=params)

    async def del_weibo(self, mid):
        params = {
            "mid": mid,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        return await self.post("https://m.weibo.cn/profile/delMyblog", params=params)

    async def get_user(self, uid):
        params = {
            "uid": uid
        }
        return await self.get(f"https://m.weibo.cn/profile/info", params=params)

    async def upload_comment_file(self, file_path):
        files = {
            "pic": (file_path, open(file_path, 'rb'), 'image/jpeg')
        }
        params = {
            "type": "json",
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        result = await self.post("https://m.weibo.cn/api/statuses/uploadPic", params=params, files=files)
        if not result:
            raise UploadError(f"上传文件错误 {result}")

        return result["pic_id"]

    async def comment_weibo(self, mid, content, file_path=""):
        params = {
            "id": mid,
            "mid": mid,
            "content": content,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }

        if file_path:
            try:
                pic_ids = await self.upload_comment_file(file_path=file_path)
            except RequestError as e:
                self.logger.error(f"文件上传失败 {e}")
                return {}
            params["picId"] = pic_ids
        return await self.post(f"https://m.weibo.cn/api/comments/create", params=params)

    async def del_comment(self, cid):
        params = {
            "cid": cid,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }

        return await self.post(f"https://m.weibo.cn/comments/destroy", params=params)

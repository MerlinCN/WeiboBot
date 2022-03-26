import asyncio
import json
import re
import traceback
from typing import Dict, Tuple, Union

import requests

from .const import *
from .exception import *
from .util import *


class NetTool:
    def __init__(self, userName: str = "", password: str = "", cookies: str = ""):
        super(NetTool, self).__init__()
        # 暂不支持用户名和密码登录 v1.0
        if userName and password:
            raise NotImplementedError("暂不支持用户名和密码登录")
        elif cookies:
            # 如果有cookies则直接使用cookies登录
            pass
        else:
            raise LoginError("登录失败!请输入cookies")
        
        self.cookies: str = cookies
        self.header: Dict[str, str] = main_header(bytes(self.cookies, encoding="utf-8"))
        self.mainSession: requests.session = requests.session()
        self.chat_header = chat_header(bytes(self.cookies, encoding="utf-8"))
        
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
        try:
            result = r.json()
            return result
        except Exception:
            raise RequestError(traceback.format_exc())
    
    async def post(self, url: str, params: Dict = None, header=None) -> Dict:
        if header is None:
            header = self.header
        r = self.mainSession.post(url, headers=header, data=params)
        if r.status_code != 200:
            raise RequestError(f"网络错误!状态码:{r.status_code}\n{r.text}")
        try:
            result = r.json()
            return result
        except Exception:
            raise RequestError(traceback.format_exc())
    
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
        except RequestError:
            if self.st_times > 5:
                self.logger.error("获取st失败!")
                st = self.header["x-xsrf-token"]
                return st
            self.st_times += 1
            await asyncio.sleep(0.5)
            return await self.st()
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
        r = self.mainSession.get(f"https://m.weibo.cn/detail/{mid}", headers=self.header)
        try:
            return json.loads(re.findall(r'(?<=render_data = \[)[\s\S]*(?=\]\[0\])', r.text)[0])["status"]
        except Exception:
            raise RequestError(traceback.format_exc())
    
    async def send_chat(self, uid: Union[str, int], content: str):
        params = {
            "uid": int(uid),
            "content": content,
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        return await self.post("https://m.weibo.cn/api/chat/send", params=params)
    
    async def user_chat(self, uid: Union[str, int], since_id: int):
        params = {"count": 20, "uid": uid, "since_id": since_id}
        return await self.get("https://m.weibo.cn/api/chat/list", params=params)
    
    async def chat_list(self, page: int):
        params = {"page": page}
        return await self.get("https://m.weibo.cn/message/msglist", params=params)
    
    async def refresh_page(self):
        self.add_ref("https://m.weibo.cn/")
        return await self.get("https://m.weibo.cn/feed/friends?")
    
    async def like(self, mid):
        self.add_ref("https://m.weibo.cn/")
        params = {
            "id": mid,
            "attitude": "heart",
            "st": await self.st(),
            "_spr": "screen:2560x1440"
        }
        return await self.post("https://m.weibo.cn/api/attitudes/create", params=params)

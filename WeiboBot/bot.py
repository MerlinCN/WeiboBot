import asyncio
from typing import Union, List, Callable

from .const import *
from .exception import *
from .message import Chat
from .net_tool import NetTool
from .user import User
from .weibo import Weibo


class Bot(User):
    def __init__(self, userName: str = "", password: str = "", cookies: str = ""):
        super(Bot, self).__init__()
        self.nettool = NetTool(userName, password, cookies)
        
        self.msg_handler: List[Callable] = []
        self.weibo_handler: List[Callable] = []
        self.weibo_read = set()
    
    async def login(self):
        login_result, self.id = await self.nettool.login()
        
        if login_result is True:
            print(f"登录成功")
        else:
            raise LoginError("登录失败")
        
        await self.init_bot_info()
    
    async def init_bot_info(self):
        raw_data = await self.nettool.user_info(self.id)
        if raw_data["ok"] == 0:
            raise RequestError("获取用户信息失败")
        self.parse(raw_data["data"]["user"])
        
        print(f"用户名:{self.screen_name},关注:{self.follow_count},粉丝:{self.followers_count},微博数量:{self.statuses_count}")
        print(f"微博简介:{self.description}")
        print(f"微博地址:{self.profile_url}")
        print(f"微博头像:{self.profile_image_url}")
        print(f"微博背景图:{self.cover_image_phone}")
    
    async def get_weibo(self, mid: Union[str, int]) -> Weibo:
        """
        获取微博实例
        
        :param mid:微博id
        :return: 微博实例
        """
        raw_data = await self.nettool.weibo_info(mid)
        oWeibo = Weibo()
        oWeibo.parse(raw_data)
        print(f"获取微博成功")
        return oWeibo
    
    async def post_weibo(self, content: str, visible: VISIBLE = VISIBLE.ALL) -> Weibo:
        """
        发布微博
        
        :param content:内容
        :param visible:可见性
        :return:新发出的微博
        """
        post_result = await self.nettool.post_weibo(content, visible)
        if post_result["ok"] == 0:
            raise RequestError(f"错误类型{post_result['errno']},{post_result['msg']}")
        oWeibo = Weibo()
        oWeibo.parse(post_result["data"])
        print(f"发送微博成功")
        return oWeibo
    
    async def repost(self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False) -> Weibo:
        """
        转发微博
        
        :param mid:微博id
        :param content:内容
        :param dualPost: 是否同时评论
        :return:新发出的微博
        """
        post_result = await self.nettool.repost_weibo(mid, content, dualPost)
        if post_result["ok"] == 0:
            raise RequestError(f"错误类型{post_result['errno']},{post_result['msg']}")
        oWeibo = Weibo()
        oWeibo.parse(post_result["data"])
        print(f"转发微博成功")
        return oWeibo
    
    async def send_chat(self, uid: Union[str, int], content: str):
        result = await self.nettool.send_chat(uid, content)
        if result["ok"] == 0:
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        oChat = Chat()
        oChat.parse(result["data"])
        return oChat
    
    async def chat_list(self, page: int = 1):
        result = await self.nettool.chat_list(page)
        if result["ok"] == 0:
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        
        return result["data"]
    
    async def chat_event(self):
        data = await self.chat_list()
        for dChat in data:
            unread = dChat["unread"]
            scheme = dChat["scheme"]
            if unread > 0 and scheme.find("gid=") == -1:
                oChat = await self.user_chat(dChat['user']["id"])
                oChat.msg_list = [oMsg for oMsg in oChat.msg_list[:unread] if oMsg.isDm()]
                for func in self.msg_handler:
                    await func(oChat)
    
    async def refresh_page(self):
        result = await self.nettool.refresh_page()
        if result["ok"] == 0:
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        
        return result["data"]
    
    async def weibo_event(self):
        result = await self.refresh_page()
        for weibo in result["statuses"]:
            if weibo["id"] in self.weibo_read:
                continue
            self.weibo_read.add(weibo["id"])
            oWeibo = Weibo()
            oWeibo.parse(weibo)
            
            for func in self.weibo_handler:
                await func(oWeibo)
    
    async def user_chat(self, uid: Union[str, int], since_id: int = 0):
        result = await self.nettool.user_chat(uid, since_id)
        if result["ok"] == 0:
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        oChat = Chat()
        oChat.parse(result["data"])
        return oChat
    
    async def like(self, mid):
        result = await self.nettool.like(mid)
        if result["ok"] == 0:
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        return result["data"]
    
    def onNewMsg(self, func):
        if func not in self.msg_handler:
            self.msg_handler.append(func)
    
    def onNewWeibo(self, func):
        if func not in self.weibo_handler:
            self.weibo_handler.append(func)
    
    async def lifecycle(self):
        await asyncio.wait_for(self.login(), timeout=10)
        while True:
            await self.chat_event()
            await self.weibo_event()
            await asyncio.sleep(1)
    
    def run(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.lifecycle())
        except KeyboardInterrupt:
            pass

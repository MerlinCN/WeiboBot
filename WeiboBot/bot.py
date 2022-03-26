import asyncio
from typing import Union, List, Callable

from .action import Action
from .const import *
from .exception import *
from .message import Chat
from .net_tool import NetTool
from .user import User
from .util import *
from .weibo import Weibo


class Bot(User):
    def __init__(self, userName: str = "", password: str = "", cookies: str = "", loop_interval=5, action_interval=30):
        super(Bot, self).__init__()
        self.nettool = NetTool(userName, password, cookies)
        
        self.msg_handler: List[Callable] = []
        self.weibo_handler: List[Callable] = []
        self.weibo_read = set()
        
        self.action_list: list[Action] = []  # 待执行的动作列表
        self.action_interval = action_interval
        self.logger = get_logger(__name__)
        self.loop_interval = loop_interval
    
    async def login(self):
        login_result, self.id = await self.nettool.login()
        
        if login_result is True:
            self.logger.info(f"登录成功")
        else:
            raise LoginError("登录失败")
        
        await self.init_bot_info()
    
    async def init_bot_info(self):
        raw_data = await self.nettool.user_info(self.id)
        if raw_data["ok"] == 0:
            raise RequestError("获取用户信息失败")
        self.parse(raw_data["data"]["user"])
        
        self.logger.info(
            f"用户名:{self.screen_name},关注:{self.follow_count},粉丝:{self.followers_count},微博数量:{self.statuses_count}")
        self.logger.info(f"微博简介:{self.description}")
        self.logger.info(f"微博地址:{self.profile_url}")
        self.logger.info(f"微博头像:{self.profile_image_url}")
        self.logger.info(f"微博背景图:{self.cover_image_phone}")
    
    async def get_weibo(self, mid: Union[str, int]) -> Weibo:
        """
        获取微博实例
        
        :param mid:微博id
        :return: 微博实例
        """
        raw_data = await self.nettool.weibo_info(mid)
        oWeibo = Weibo()
        oWeibo.parse(raw_data)
        return oWeibo
    
    async def _post(self, content: str, visible: VISIBLE = VISIBLE.ALL) -> Weibo:
        """
        发布微博
        
        :param content:内容
        :param visible:可见性
        :return:新发出的微博
        """
        result = await self.nettool.post_weibo(content, visible)
        self.check_result(result)
        oWeibo = Weibo()
        oWeibo.parse(result["data"])
        self.logger.info(f"发送微博成功")
        return oWeibo
    
    def check_result(self, result: dict):
        if result["ok"] == 0:
            if result.get("errno", 0) in WEIBO_WARNING:
                self.logger.warning(f"错误类型{result['errno']},{result['msg']}")
            raise RequestError(f"错误类型{result['errno']},{result['msg']}")
    
    def post_action(self, content: str, visible: VISIBLE = VISIBLE.ALL):
        self.action_list.append(Action(self._post, content, visible))
    
    def repost_action(self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False):
        self.action_list.append(Action(self._repost, mid, content, dualPost))
    
    async def _repost(self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False) -> Weibo:
        """
        转发微博
        
        :param mid:微博id
        :param content:内容
        :param dualPost: 是否同时评论
        :return:新发出的微博
        """
        result = await self.nettool.repost_weibo(mid, content, dualPost)
        self.check_result(result)
        oWeibo = Weibo()
        oWeibo.parse(result["data"])
        self.logger.info(f"转发微博成功")
        return oWeibo
    
    async def send_chat(self, uid: Union[str, int], content: str):
        result = await self.nettool.send_chat(uid, content)
        self.check_result(result)
        oChat = Chat()
        oChat.parse(result["data"])
        return oChat
    
    async def chat_list(self, page: int = 1):
        result = await self.nettool.chat_list(page)
        self.check_result(result)
        return result["data"]
    
    async def chat_event(self):
        try:
            data = await self.chat_list()
            for dChat in data:
                unread = dChat["unread"]
                scheme = dChat["scheme"]
                if unread > 0 and scheme.find("gid=") == -1:
                    oChat = await self.user_chat(dChat['user']["id"])
                    oChat.msg_list = [oMsg for oMsg in oChat.msg_list[:unread] if oMsg.isDm()]
                    for func in self.msg_handler:
                        await func(oChat)
        except RequestError as e:
            self.logger.warning(f"获取聊天列表失败:{e}")
            return
    
    async def refresh_page(self):
        result = await self.nettool.refresh_page()
        self.check_result(result)
        return result["data"]
    
    async def weibo_event(self):
        try:
            result = await self.refresh_page()
        except RequestError as e:  # 刷新页面失败,可跳过此次刷新
            self.logger.warning(e)
            return
        for weibo in result["statuses"]:
            if weibo["id"] in self.weibo_read:
                continue
            self.weibo_read.add(weibo["id"])
            oWeibo = await self.get_weibo(weibo["id"])
            for func in self.weibo_handler:
                await func(oWeibo)
    
    async def user_chat(self, uid: Union[str, int], since_id: int = 0):
        result = await self.nettool.user_chat(uid, since_id)
        self.check_result(result)
        oChat = Chat()
        oChat.parse(result["data"])
        return oChat
    
    async def like_weibo(self, mid):
        result = await self.nettool.like(mid)
        self.check_result(result)
        return result["data"]
    
    def onNewMsg(self, func):
        if func not in self.msg_handler:
            self.msg_handler.append(func)
    
    def onNewWeibo(self, func):
        if func not in self.weibo_handler:
            self.weibo_handler.append(func)
    
    async def run_action(self):
        """
        执行所有的action
        如果成功或者超过最大尝试次数，则删除action
        
        :return:
        """
        for action in self.action_list:
            result, status = await action.run()
            if status == ACTION.MAX_TRY or status == ACTION.DONE:
                self.action_list.remove(action)
            
            await asyncio.sleep(self.action_interval)
    
    async def lifecycle(self):
        await asyncio.wait_for(self.login(), timeout=10)
        while True:
            await asyncio.gather(
                self.chat_event(),
                self.weibo_event(),
                self.run_action(),
            )
            self.logger.info("Heartbeat")
            await asyncio.sleep(self.loop_interval)
    
    def run(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.lifecycle())
        except KeyboardInterrupt:
            pass

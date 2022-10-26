import asyncio
import time
from typing import Union, List, Callable
from types import FunctionType

from tinydb import TinyDB, Query

from .action import Action
from .comment import Comment
from .const import *
from .exception import *
from .message import Chat
from .net_tool import NetTool
from .user import User
from .util import *
from .weibo import Weibo


class Bot(User):
    def __init__(self, username: str = "", password: str = "", cookies: str = "", loop_interval=1, action_interval=1,
                 is_debug=False
                 ):
        super(Bot, self).__init__()
        self.nettool = NetTool(username, password, cookies)

        self.msg_handler: List[FunctionType] = []
        self.weibo_handler: List[FunctionType] = []
        self.mention_cmt_handler: List[FunctionType] = []
        self.tick_handler: List[FunctionType] = []
        self.weibo_read = set()
        self.is_debug = is_debug
        self.action_list: list[Action] = []  # 待执行的动作列表
        self.action_interval = action_interval
        self.logger = get_logger(__name__, is_debug)
        self.loop_interval = loop_interval
        self.db = TinyDB('WeiboBotDB.json')

    # region 数据库操作
    def is_weibo_read(self, mid: Union[str, int]) -> bool:
        weibo_read = self.db.table("weibo_read")
        q = Query()
        mid = int(mid)
        return bool(weibo_read.search(q.mid == mid))

    def mark_weibo(self, mid: Union[str, int]):
        mid = int(mid)
        weibo_read = self.db.table("weibo_read")
        weibo_read.insert({"mid": mid})

    def is_mention_cmt_read(self, mid: Union[str, int]) -> bool:
        mention_cmt_read = self.db.table("mention_cmt_read")
        q = Query()
        mid = int(mid)
        return bool(mention_cmt_read.search(q.mid == mid))

    def mark_mention_cmt(self, mid: Union[str, int]):
        mid = int(mid)
        mention_cmt_read = self.db.table("mention_cmt_read")
        mention_cmt_read.insert({"mid": mid})

    def is_weibo_repost(self, mid: Union[str, int]) -> bool:
        """
        判断微博是否转发

        :param mid: 微博id
        :return: True/False
        """
        weibo_repost = self.db.table("weibo_repost")
        q = Query()
        mid = int(mid)
        return bool(weibo_repost.search(q.mid == mid))

    def mark_weibo_repost(self, mid: Union[str, int]):
        mid = int(mid)
        weibo_repost = self.db.table("weibo_repost")
        weibo_repost.insert({"mid": mid})

    # endregion
    async def login(self):
        login_result, self.id = await self.nettool.login()

        if login_result is True:
            self.logger.info(f"登录成功")
        else:
            raise LoginError("登录失败")

        await self.init_bot_info()

        return True

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

    async def get_weibo(self, mid: Union[str, int]) -> Union[Weibo, None]:
        """
        获取微博实例

        :param mid:微博id
        :return: 微博实例
        """
        try:
            raw_data = await self.nettool.weibo_info(mid)
        except RequestError:
            self.logger.error(f"获取微博 {mid} 失败")
            return None
        weibo = Weibo()
        weibo.parse(raw_data)
        return weibo

    async def post_weibo(self, content: str, visible: VISIBLE = VISIBLE.ALL) -> Union[Weibo, None]:
        """
        发布微博

        :param content:内容
        :param visible:可见性
        :return:新发出的微博
        """
        result = await self.nettool.post_weibo(content, visible)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"发送微博错误 {content} {result} {e}")
            return None
        weibo = Weibo()
        weibo.parse(result["data"])
        self.logger.info(f"发送微博成功 {weibo.detail_url()}")
        return weibo

    def check_result(self, result: dict):
        if result["ok"] == 0:
            try:
                err = WEIBO_ERR(result.get("errno", 0))
            except ValueError as e:
                err = 0
            if err == WEIBO_ERR.NO_EXIST:
                raise NoExistError(f"微博不存在或暂无查看权限")
            elif err == WEIBO_ERR.NO_CONTENT:
                return True
            else:
                raise RequestError(f"错误类型{result['errno']},{result['msg']}")
        elif result["ok"] == -100:
            raise LoginError(f"Cookies已过期，请重新登录")
        return True

    def post_action(self, content: str, visible: VISIBLE = VISIBLE.ALL):
        self.action_list.append(Action(self.post_weibo, content, visible))

    def repost_action(self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False):
        for action in self.action_list:
            if mid in action.args:
                self.logger.info(f"动作序列中已存在{mid}的转发动作")
                return
        self.action_list.append(Action(self.repost_weibo, mid, content, dualPost))

    async def repost_weibo(self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False) -> Union[
        Weibo, None]:
        """
        转发微博

        :param mid:微博id
        :param content:内容
        :param dualPost: 是否同时评论
        :return:新发出的微博
        """
        result = await self.nettool.repost_weibo(mid, content, dualPost)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"转发微博错误 {mid} {result} {e}")
            return None
        weibo = Weibo()
        weibo.parse(result["data"])
        self.mark_weibo_repost(mid)
        self.logger.info(f"转发微博 {weibo.detail_url()} 成功")
        return weibo

    async def send_message(self, uid: Union[str, int], content: str = "", file_path: str = "") -> Union[Chat, None]:
        """
        私信并返回聊天对象

        :param uid:角色id
        :param content:文本内容
        :param file_path:附件
        :return: 聊天对象
        """
        result = await self.nettool.send_message(uid, content, file_path)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"私信错误 {uid} {result} {e}")
            return None
        chat = Chat()
        chat.parse(result["data"])
        self.logger.info(f"私信成功")
        return chat

    async def comment_weibo(self, mid: Union[str, int], content: str = "", file_path: str = "") -> Union[Comment, None]:
        result = await self.nettool.comment_weibo(mid, content, file_path)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"评论错误 {mid} {result} {e}")
            return None
        cmt = Comment()
        cmt.parse(result["data"])
        self.logger.info(f"评论成功 {cmt.root_weibo.detail_url()}#{cmt.id}")
        return cmt

    async def del_comment(self, cid) -> int:
        """
        删除某条评论

        :param cid: 评论id
        :return:返回的json字典
        """
        result = await self.nettool.del_comment(cid)
        self.logger.info(f"删除评论 {cid} 成功")
        return result["ok"]

    async def chat_list(self, page: int = 1):
        result = await self.nettool.chat_list(page)
        if not result:
            return []
        self.check_result(result)
        return result["data"]

    async def mentions_cmt_list(self, page: int = 1) -> List[Comment]:
        result = await self.nettool.mentions_cmt(page)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"获取@我的评论 错误 {page} {result} {e}")
            return []
        result_list = []
        if not result_list:
            return result_list
        for dCmt in result["data"]:
            cmt = Comment()
            cmt.parse(dCmt)
            result_list.append(cmt)
        return result_list

    async def mentions_cmt_event(self):
        try:
            cmt_list = await self.mentions_cmt_list()
        except RequestError as e:
            self.logger.warning(f"获取@我的评论失败:{e}")
            return
        for cmt in cmt_list:
            if self.is_mention_cmt_read(cmt.mid):
                continue
            for func in self.mention_cmt_handler:
                try:
                    await func(cmt)
                except Exception as e:
                    self.logger.error(f"处理@我的评论回调 {func.__name__} 失败:{e}")
                    continue
            self.mark_mention_cmt(cmt.mid)

    async def chat_event(self):
        try:
            data = await self.chat_list()
        except Exception as e:
            self.logger.warning(f"获取聊天列表失败:{e}")
            return
        for dChat in data:
            unread = dChat["unread"]
            scheme = dChat["scheme"]
            if unread > 0 and scheme.find("gid=") == -1:
                try:
                    oChat = await self.user_chat(dChat['user']["id"])
                except Exception as e:
                    self.logger.warning(f"获取聊天失败:{e}")
                    continue
                oChat.msg_list = [oMsg for oMsg in oChat.msg_list[:unread] if oMsg.isDm()]
                for func in self.msg_handler:
                    try:
                        await func(oChat)
                    except Exception as e:
                        self.logger.error(f"处理聊天回调 {func.__name__} 失败:{e}")
                        continue

    async def refresh_page(self, max_id=0):
        try:
            result = await self.nettool.refresh_page(max_id)
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"获取主页错误 {max_id} {e}")
            return {}
        return result["data"]

    async def solve_weibo(self, mid: Union[str, int]):
        weibo = await self.get_weibo(mid)
        for func in self.weibo_handler:
            try:
                await func(weibo)
            except Exception as e:
                self.logger.error(f"处理微博回调 {func.__name__} 失败:{e}")
                continue

    async def _scan_page(self, result: dict):
        for weibo in result["statuses"]:
            await self.chat_event()
            if self.is_weibo_read(weibo["id"]):
                continue
            try:
                await self.solve_weibo(weibo["id"])
            except Exception as e:
                self.logger.warning(f"获取微博失败:{e}")
                continue
            self.mark_weibo(weibo["id"])

    async def scan_pages(self, page: int = 1):
        page_cnt = 0
        last_weibo_id = 0
        while True:
            if page_cnt >= page:
                if self.action_list:
                    self.logger.info(f"正在处理剩余操作{len(self.action_list)}")
                    continue
                else:
                    self.logger.info("扫描完成")
                    break
            await self.run_action()
            try:
                result = await self.refresh_page(last_weibo_id)
                await self._scan_page(result)
                page_cnt += 1
                self.logger.info("第%d页获取成功" % page_cnt)
                last_weibo_id = result["statuses"][-1]["id"]
            except Exception as e:
                await asyncio.sleep(1)
                continue

    async def weibo_event(self):
        result = await self.refresh_page()
        if not result:
            return
        await self._scan_page(result)

    async def user_chat(self, uid: Union[str, int], since_id: int = 0) -> Union[Chat, None]:
        result = await self.nettool.user_chat(uid, since_id)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"获取聊天记录错误 {uid} {result} {e}")
            return
        chat = Chat()
        chat.parse(result["data"])
        return chat

    async def like_weibo(self, mid) -> dict:
        """
        点赞某条微博

        :param mid: 微博id
        :return:返回的json字典
        """
        result = await self.nettool.like(mid)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"点赞错误 {mid} {result} {e}")
            return {}
        self.logger.info(f"点赞微博 {mid} 成功")
        return result["data"]

    async def del_weibo(self, mid) -> int:
        """
        删除自己某条微博

        :param mid: 微博id
        :return:返回的json字典
        """
        result = await self.nettool.del_weibo(mid)
        self.logger.info(f"删除微博 {mid} 成功")
        return result["ok"]

    async def get_user(self, uid) -> Union[User, None]:
        """
        获取微博用户对象

        :param uid: 用户id
        :return: 用户对象
        """
        result = await self.nettool.get_user(uid)
        try:
            self.check_result(result)
        except Exception as e:
            self.logger.error(f"获取用户错误 {uid} {result} {e}")
            return
        user = User()
        user.parse(result["data"]["user"])

        for status in result["data"]["statuses"]:
            weibo = Weibo()
            weibo.parse(status)
            user.latest_weibo.append(weibo)

        return user

    # region 事件装饰器
    def onNewMsg(self, func: FunctionType):
        if func not in self.msg_handler:
            self.msg_handler.append(func)

    def onNewWeibo(self, func: FunctionType):
        if func not in self.weibo_handler:
            self.weibo_handler.append(func)

    def onMentionCmt(self, func: FunctionType):
        if func not in self.mention_cmt_handler:
            self.mention_cmt_handler.append(func)

    def onTick(self, func: FunctionType):
        if func not in self.tick_handler:
            self.tick_handler.append(func)

    # endregion

    async def tick(self):
        for func in self.tick_handler:
            try:
                await func()
            except Exception as e:
                self.logger.error(f"tick处理失败:{e}")
                continue

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
                self.mentions_cmt_event(),
                self.tick(),
                self.run_action(),
            )
            self.logger.info("Heartbeat")

    def run(self):
        try:
            asyncio.run(self.lifecycle())
        except KeyboardInterrupt:
            self.db.close()

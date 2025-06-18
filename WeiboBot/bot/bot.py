import asyncio
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from loguru import logger

from WeiboBot.bot.event import EventManager
from WeiboBot.data import MentionCmtRead, WeiboRead, WeiboRepost, init_db
from WeiboBot.model import Chat, User, Weibo
from WeiboBot.net import NetTool


def interval_control(interval: float):
    """控制函数执行间隔的装饰器

    Args:
        interval (float): 执行间隔（秒）
    """
    last_run = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            now = time.time()
            func_name = func.__name__

            # 如果是第一次执行或者已经超过间隔时间
            if func_name not in last_run or now - last_run[func_name] >= interval:
                last_run[func_name] = now
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class Bot(NetTool):
    def __init__(
        self,
        cookies: Union[str, dict, Path] = Path("weibobot_cookies.json"),
        db_path: Path = "weibo_bot.db",
    ):
        super(Bot, self).__init__(cookies)
        self.event_manager = EventManager()
        self.weibo_read = set()
        self.db_path: Path = db_path
        self.mid: int = 0
        self.bot_info: Optional[User] = None

    async def __aenter__(self):
        await init_db(self.db_path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

    # region 数据库操作
    async def is_weibo_read(self, mid: Union[str, int]) -> bool:
        weibo_read = await WeiboRead.get_by_mid(mid)
        return weibo_read is not None

    async def mark_weibo(self, mid: Union[str, int]):
        mid = int(mid)
        await WeiboRead.create_record(mid)

    async def is_mention_cmt_read(self, mid: Union[str, int]) -> bool:
        mention_cmt_read = await MentionCmtRead.get_by_mid(mid)
        return mention_cmt_read is not None

    async def mark_mention_cmt(self, mid: Union[str, int]):
        mid = int(mid)
        await MentionCmtRead.create_record(mid)

    async def is_weibo_repost(self, mid: Union[str, int]) -> bool:
        weibo_repost = await WeiboRepost.get_by_mid(mid)
        return weibo_repost is not None

    async def mark_weibo_repost(self, mid: Union[str, int]):
        mid = int(mid)
        await WeiboRepost.create_record(mid)

    # endregion

    # region 事件处理函数
    @interval_control(5)  # 聊天检查间隔30秒
    async def chat_loop(self):
        chat_list: List[Chat] = await self.chat_list()
        for chat in chat_list:
            if chat.unread > 0 and chat.scheme.find("gid") == -1:
                chat_detail = await self.user_chat(chat.user.id)
                if chat_detail is None:
                    logger.warning(f"获取聊天失败:{chat.id}")
                    continue
                chat_detail.msgs = [
                    msg for msg in chat_detail.msgs[: chat.unread] if msg.dm_type == 1
                ]
                for _, func in self.event_manager.msg_handler:
                    await func(chat_detail)

    @interval_control(5)  # @评论检查间隔10分钟
    async def mentions_cmt_loop(self):
        cmt_list = await self.mentions_cmt()
        for cmt in cmt_list:
            if await self.is_mention_cmt_read(cmt.mid):
                continue
            for _, func in self.event_manager.mention_cmt_handler:
                await func(cmt)
            await self.mark_mention_cmt(cmt.mid)

    @interval_control(5)  # 页面扫描间隔5秒
    async def scan_pages_loop(self):
        page = await self.refresh_page()
        if not page or not page.statuses:
            return
        for weibo in page.statuses:
            if await self.is_weibo_read(weibo.id):
                continue
            for _, func in self.event_manager.weibo_handler:
                await func(weibo)
            await self.mark_weibo(weibo.id)

    @interval_control(1)  # 定时任务间隔1秒
    async def tick_loop(self):
        for _, func in self.event_manager.tick_handler:
            await func()

    # endregion

    # region 重载功能

    async def login(self) -> int:
        self.mid = await super().login()
        return self.mid

    async def repost_weibo(
        self, mid: Union[str, int], content: str = "转发微博", dualPost: bool = False
    ) -> Union[Weibo, None]:
        result = await super().repost_weibo(mid, content, dualPost)
        await self.mark_weibo_repost(mid)
        return result

    # endregion

    # region 事件装饰器
    def onNewMsg(self, priority: int = 0):
        return self.event_manager.onNewMsg(priority)

    def onNewWeibo(self, priority: int = 0):
        return self.event_manager.onNewWeibo(priority)

    def onMentionCmt(self, priority: int = 0):
        return self.event_manager.onMentionCmt(priority)

    def onTick(self, priority: int = 0):
        return self.event_manager.onTick(priority)

    # endregion

    # region 生命周期管理
    async def lifecycle(self):
        await init_db(self.db_path)
        mid = await self.login()
        if mid == 0:
            logger.error("登录失败")
            await self.login_by_qr_code()
            await self.check_login_status()
        while True:
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        self.chat_loop(),
                        self.scan_pages_loop(),
                        self.mentions_cmt_loop(),
                        self.tick_loop(),
                    ),
                    timeout=30,
                )
                logger.debug("Heartbeat - 所有事件处理完成")
            except asyncio.TimeoutError:
                logger.warning("事件处理超时")
            finally:
                await asyncio.sleep(1)

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.lifecycle())
        except KeyboardInterrupt:
            logger.info("收到退出信号，正在关闭...")
            loop.close()
            logger.info("已安全退出")

    # endregion

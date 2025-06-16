from typing import Awaitable, Callable, List, Tuple, TypeAlias

from WeiboBot.model import Chat, Comment, Weibo

# 定义类型别名
MessageHandler: TypeAlias = Callable[[Chat], Awaitable[None]]
WeiboHandler: TypeAlias = Callable[[Weibo], Awaitable[None]]
MentionCommentHandler: TypeAlias = Callable[[Comment], Awaitable[None]]
TickHandler: TypeAlias = Callable[[], Awaitable[None]]


class EventManager:
    def __init__(self):
        self.msg_handler: List[Tuple[int, Callable]] = []
        self.weibo_handler: List[Tuple[int, Callable]] = []
        self.mention_cmt_handler: List[Tuple[int, Callable]] = []
        self.tick_handler: List[Tuple[int, Callable]] = []

    def onNewMsg(self, priority: int = 10):
        """注册新消息处理函数

        Args:
            priority (int, optional): 优先级，数字越大优先级越高. 默认为10.

        Returns:
            Callable: 装饰器函数
        """

        def decorator(func: Callable):
            self.msg_handler.append((priority, func))
            # 按优先级降序排序
            self.msg_handler.sort(key=lambda x: x[0], reverse=True)
            return func

        return decorator

    def onNewWeibo(self, priority: int = 10):
        """注册新微博处理函数

        Args:
            priority (int, optional): 优先级，数字越大优先级越高. 默认为10.

        Returns:
            Callable: 装饰器函数
        """

        def decorator(func: Callable):
            self.weibo_handler.append((priority, func))
            # 按优先级降序排序
            self.weibo_handler.sort(key=lambda x: x[0], reverse=True)
            return func

        return decorator

    def onMentionCmt(self, priority: int = 10):
        """注册@评论处理函数

        Args:
            priority (int, optional): 优先级，数字越大优先级越高. 默认为10.

        Returns:
            Callable: 装饰器函数
        """

        def decorator(func: Callable):
            self.mention_cmt_handler.append((priority, func))
            # 按优先级降序排序
            self.mention_cmt_handler.sort(key=lambda x: x[0], reverse=True)
            return func

        return decorator

    def onTick(self, priority: int = 10):
        """注册定时任务处理函数

        Args:
            priority (int, optional): 优先级，数字越大优先级越高. 默认为10.

        Returns:
            Callable: 装饰器函数
        """

        def decorator(func: Callable):
            self.tick_handler.append((priority, func))
            # 按优先级降序排序
            self.tick_handler.sort(key=lambda x: x[0], reverse=True)
            return func

        return decorator

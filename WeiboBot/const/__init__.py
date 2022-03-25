from enum import Enum

__all__ = ["VISIBLE", "MSG", "ACTION", "WEIBOERR","WEIBO_WARNING"]


class VISIBLE(Enum):
    ALL = 0  # 全部
    ONLY_ME = 1  # 仅自己可见
    FRIENDS = 6  # 仅好友可见
    FOLLOWERS = 10  # 仅关注人可见


class MSG(Enum):
    NORMAL = 1  # 普通消息
    SUBSCRIPTION = 4  # 订阅消息


class ACTION(Enum):
    UNDONE = 0  # 未完成
    RUNNING = 1  # 运行中
    DONE = 2  # 已完成
    FAILED = 3  # 失败
    MAX_TRY = 4  # 超过最大尝试次数


class WEIBOERR(Enum):
    NO_DATA = 100011  # 没有数据


WEIBO_WARNING = [WEIBOERR.NO_DATA.value]

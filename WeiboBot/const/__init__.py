from enum import Enum

__all__ = ["VISIBLE", "MSG"]


class VISIBLE(Enum):
    ALL = 0  # 全部
    MYSELF = 1  # 仅自己可见
    FRIENDS = 6  # 仅好友可见
    FOLLOWERS = 10  # 仅关注人可见


class MSG(Enum):
    NORMAL = 1  # 普通消息
    SUBSCRIPTION = 4  # 订阅消息

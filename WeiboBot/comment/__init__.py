from WeiboBot.util import *
from WeiboBot.weibo import Weibo
from WeiboBot.user import User
from typing import Union


class Comment:
    def __init__(self):
        self.disable_reply = IntField()  # 关闭回复
        self.created_at = StrField()  # 创建时间
        self.id = StrField()  # 评论id
        self.rootid = StrField()  # 评论的原微博id
        self.rootidstr = StrField()  # 评论的原微博id字符串
        self.floor_number = IntField()  # 楼层数
        self.text = StrField()  # 评论内容
        self.restrictOperate = IntField()  # 是否可以删除
        self.source = StrField()  # 评论来源
        self.comment_badge = ListField()  # 评论徽章
        self.user = DictField()  # 评论用户
        self.mid = StrField()  # 评论的微博id
        self.status = DictField()  # 评论的微博
        self.like_count = IntField()  # 点赞数
        self.reply_count = IntField()  # 回复数
        self.liked = BoolField()  # 是否点赞
        self.gid = IntField()  # 分组id
        self.feature_type = IntField()  # 特殊徽章类型
        self.cut_tail = BoolField()  # 是否截断
        self.bid = StrField()
        self.reply_original_text = StrField()  # 回复原文
        self.feedback_menu_type = IntField()  # 回复菜单类型

        self.logger = get_logger(__name__)
        self.root_weibo: Union[Weibo, None] = None
        self.sender: Union[User, None] = None

    def parse(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.debug(f'{k} is not a valid attribute, type is {type(v)}')

        if data["status"]:
            weibo = Weibo()
            weibo.parse(data["status"])
            self.root_weibo = weibo
        else:
            self.logger.warning(f'status is not a valid attribute')

        if data["user"]:
            user = User()
            user.parse(data["user"])
            self.sender = user
        else:
            self.logger.warning(f'user is not a valid attribute')

from typing import Dict
from WeiboBot.weibo import Weibo
from WeiboBot.util import *


class User:

    def __init__(self):
        self.id = IntField()  # 用户id
        self.screen_name = StrField()  # 用户昵称
        self.profile_image_url = StrField()  # 用户头像
        self.profile_url = StrField()  # 用户主页
        self.statuses_count = IntField()  # 微博数
        self.verified = BoolField()  # 是否是微博认证用户
        self.verified_type = IntField()  # 认证类型
        self.close_blue_v = BoolField()  # 是否关注微博蓝V
        self.description = BoolField()  # 用户描述
        self.gender = StrField()  # 性别
        self.mbtype = IntField()
        self.urank = IntField()
        self.mbrank = IntField()
        self.follow_me = IntField()  # 是否关注我
        self.following = IntField()  # 我是否关注
        self.follow_count = IntField()  # 关注数
        self.followers_count = StrField()  # 粉丝数
        self.followers_count_str = StrField()  # 粉丝数
        self.cover_image_phone = StrField()  # 主页头图
        self.avatar_hd = StrField()  # 高清头像
        self.like = BoolField()  # 是否喜欢
        self.like_me = BoolField()  # 是否喜欢我
        self.badge = DictField()  # 徽章
        self.verified_type_ext = IntField()  # 认证类型扩展
        self.verified_reason = StrField()  # 认证原因

        self.latest_weibo: list[Weibo] = []
        self.logger = get_logger(__name__)

    def parse(self, info: Dict):
        for k, v in info.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.debug(f'{k} is not a valid attribute, type is {type(v)}')

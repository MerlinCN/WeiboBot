from typing import List, Dict

from WeiboBot.user import User
from WeiboBot.util import *
from .message import Message


class Chat:
    def __init__(self):
        self.following = BoolField()  # 是否关注
        self.last_read_mid = IntField()  #
        self.title = StrField()  # 标题
        self.total_number = IntField()  # 总数
        self.users = DictField()
        
        self.user_dict: Dict[int, User] = {}
        self.msg_list: List[Message] = []
        
        self.logger = get_logger(__name__)
        
    def parse(self, data):
        for k, v in data.items():
            if k == "msgs":
                continue
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.debug(f'{k} is not a valid attribute, type is {type(v)}')
        
        if data["msgs"]:
            for v in data["msgs"]:
                msg = Message()
                msg.parse(v)
                self.msg_list.append(msg)
        if data["users"]:
            for k, v in data["users"].items():
                user = User()
                user.parse(v)
                self.user_dict[int(k)] = user
    
    def since_id(self):
        if self.msg_list:
            return self.msg_list[0].id
        return 0

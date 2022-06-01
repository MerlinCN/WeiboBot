from WeiboBot.const import *
from WeiboBot.util import *


class Message:
    def __init__(self):
        self.created_at = StrField()  #
        self.dm_type = IntField()  #
        self.id = StrField()  #
        self.media_type = IntField()  #
        self.msg_status = IntField()  #
        self.recipient_id = StrField()  # 收件人id
        self.recipient_screen_name = StrField()  # 收件人的昵称
        self.sender_id = StrField()  # 发送者id
        self.sender_screen_name = StrField()  # 发送者的昵称
        self.text = StrField()  # 内容
        self.attachment = DictField()  # 附件
        
        self.logger = get_logger(__name__)
    
    def parse(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.debug(f'{k} is not a valid attribute, type is {type(v)}')
    
    def isDm(self):
        """
        判断是否是私信
        :return:
        """
        return self.dm_type == MSG.NORMAL.value
    
    def isSubscription(self):
        """
        判断是否是订阅
        :return:
        """
        return self.dm_type == MSG.SUBSCRIPTION.value

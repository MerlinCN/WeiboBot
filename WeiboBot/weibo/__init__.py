from typing import Union, List

from WeiboBot.util import *


class Weibo:
    def __init__(self):
        # region 基本信息
        self.visible = DictField()  # 微博的可见性及指定可见分组信息
        self.created_at = StrField()  # 微博创建时间
        self.id = StrField()  # 微博ID
        self.mid = StrField()  # 微博MID
        self.can_edit = BoolField()  # 是否可以编辑
        self.show_additional_indication = IntField()  # 是否显示额外信息
        self.text = StrField()  # 微博信息内容
        self.textLength = IntField()  # 微博信息内容字数
        self.source = StrField()  # 微博来源
        self.favorited = BoolField()  # 是否已收藏
        self.pic_ids = ListField()  # 微博的配图ID
        self.pic_types = StrField()  # 微博的配图类型
        self.pic_focus_point = ListField()  # 微博的配图中心点
        self.falls_pic_focus_point = ListField()  # 微博的配图中心点
        self.pic_rectangle_object = ListField()  # 微博的配图框
        self.pic_flag = IntField()  # 微博的配图标记
        self.thumbnail_pic = StrField()  # 微博的缩略图
        self.bmiddle_pic = StrField()  # 微博的中等尺寸图片
        self.original_pic = StrField()  # 微博的原始图片
        self.is_paid = BoolField()  # 是否付费
        self.mblog_vip_type = IntField()  # 微博的会员类型
        self.user = DictField()  # 微博作者的用户信息字段
        self.picStatus = StrField()  # 微博的配图状态
        self.reposts_count = IntField()  # 转发数
        self.comments_count = IntField()  # 评论数
        self.reprint_cmt_count = IntField()  # 转发评论数
        self.attitudes_count = IntField()  # 赞数
        self.pending_approval_count = IntField()  # 待审核数
        self.isLongText = BoolField()  #
        self.liked = BoolField()  # 是否已赞
        self.like_attitude_type = IntField()  # 点赞类型
        self.reward_exhibition_type = IntField()  # 打赏模块展示类型
        self.hide_flag = IntField()  # 隐藏类型
        self.mlevel = IntField()  # 微博等级
        self.darwin_tags = ListField()  # 微博的标签
        self.mblogtype = IntField()  # 微博类型
        self.more_info_type = IntField()  # 更多信息类型
        self.cardid = StrField()  # 卡片ID
        self.number_display_strategy = DictField()  #
        self.enable_comment_guide = BoolField()  #
        self.content_auth = IntField()  #
        self.pic_num = IntField()  #
        self.alchemy_params = DictField()  #
        self.reprint_type = IntField()  #
        self.can_reprint = BoolField()  #
        self.new_comment_style = IntField()  #
        self.page_info = DictField()  #
        self.pics = ListField()  #
        self.bid = StrField()  #
        self.status_title = StrField()  #
        self.ok = IntField()  #
        self.scheme = StrField()  #
        self.tipScheme = StrField()  #
        self.raw_text = StrField()  #
        self.title = DictField()  #
        self.repost_type = IntField()  #
        self.retweeted_status = DictField()  #
        self.edit_count = IntField()  #
        self.edit_at = StrField()  #
        self.version = IntField()  #
        self.gif_videos = ListField()  #
        self.reads = IntField()  # 阅读数
        self.rid = StrField()  #
        self.safe_tags = IntField()  #
        self.fid = IntField()  #
        self.pic_video = StrField()  #
        self.live_photo = ListField()  #
        self.pid = IntField()  #
        self.pidstr = StrField()  #
        self.jump_type = IntField()  #
        self.topic_id = StrField()  #
        self.sync_mblog = BoolField()  #
        self.is_imported_topic = BoolField()  #
        self.longText = DictField()
        self.mark = StrField()  #
        self.reward_scheme = StrField()
        self.state = IntField()  #
        self.expire_time = IntField()  #
        self.deleted = StrField()  #
        self.ad_state = IntField()  #
        self.verified_type_ext = IntField()
        self.verified_reason = StrField()
        self.mlevelSource = StrField()
        self.ipRegion = StrField()
        self.stickerID = StrField()
        self.filterID = StrField()
        self.buttons = ListField()
        self.is_vote = IntField()
        self.comment_manage_info = DictField()
        self.attitude_dynamic_adid = StrField()
        # endregion

        self.original_weibo: Union[Weibo, None] = None
        self.logger = get_logger(__name__)

    def parse(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.debug(f'{k} is not a valid attribute, type is {type(v)}, id is {self.id}')

        if self.retweeted_status != {}:
            self.original_weibo = Weibo()
            self.original_weibo.parse(self.retweeted_status)

    def detail_url(self) -> str:
        return f"https://m.weibo.cn/detail/{self.id}"

    def full_text(self) -> str:
        """
        未格式化的原文本
        :return:
        """
        if self.longText != {}:
            return self.longText['longTextContent']
        else:
            return self.text

    def weibo_id(self) -> int:
        return int(self.id)

    def user_uid(self) -> int:
        return int(self.user["id"])

    def video_url(self) -> str:
        url = ""
        if self.page_info.get("type", "") == "video" and "urls" in self.page_info:
            url = list(self.page_info["urls"].values())[0]
        return url

    def image_list(self) -> List[str]:
        return [img["large"]["url"] for img in self.pics]

    def thumbnail_image_list(self) -> List[str]:
        return [img["url"] for img in self.pics]  # 微博图片(缩略图)

    def is_visible(self) -> bool:
        return self.visible.get('type', 0) == 0

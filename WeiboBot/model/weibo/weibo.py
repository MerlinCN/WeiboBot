from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from ..base import MetaBaseModel


if TYPE_CHECKING:
    from ..user import User
    from ..comment import Comment


class Weibo(MetaBaseModel):
    """微博模型，只保留最常用的字段"""

    visible: dict = Field(description="微博的可见性及指定可见分组信息")
    created_at: str = Field(description="微博创建时间")
    id: str = Field(description="微博ID")
    mid: str = Field(description="微博MID")
    text: str = Field(description="微博信息内容")
    source: Optional[str] = Field(default="", description="微博来源")
    user: Optional["User"] = Field(default=None, description="微博作者的用户信息字段")
    reposts_count: Optional[int] = Field(default=0, description="转发数")
    comments_count: Optional[int] = Field(default=0, description="评论数")
    attitudes_count: Optional[int] = Field(default=0, description="赞数")
    isLongText: Optional[bool] = Field(default=False, description="是否长文本")
    liked: Optional[bool] = Field(default=False, description="是否已赞")
    pics: Optional[list[dict]] = Field(default_factory=list, description="配图")
    page_info: Optional[dict] = Field(default_factory=dict, description="页面信息")
    longText: Optional[dict] = Field(default_factory=dict, description="长文本")
    deleted: Optional[str] = Field(default="0", description="是否已删除")
    retweeted_status: Optional["Weibo"] = Field(default=None, description="原始微博")
    comments: Optional[List["Comment"]] = Field(default=None, description="评论列表")
    live_photo: Optional[list[str]] = Field(
        default_factory=list, description="livephoto"
    )

    metadata: Optional[dict] = Field(default=None, description="原始数据")

    def detail_url(self) -> str:
        """获取微博详情页URL"""
        return f"https://m.weibo.cn/detail/{self.id}"

    def full_text(self) -> str:
        """获取完整文本内容"""
        if self.longText != {}:
            return self.longText["longTextContent"]
        else:
            return self.text

    def weibo_id(self) -> int:
        """获取微博ID（整数形式）"""
        return int(self.id)

    def user_uid(self) -> int:
        """获取用户ID"""
        return int(self.user["id"])

    def video_url(self) -> str:
        """获取视频URL"""
        url = ""
        if self.page_info.get("type", "") == "video" and "urls" in self.page_info:
            url = list(self.page_info["urls"].values())[0]
        return url

    def image_list(self) -> List[str]:
        """获取图片URL列表"""
        return [img["large"]["url"] for img in self.pics] if self.pics else []

    def thumbnail_image_list(self) -> List[str]:
        """获取缩略图URL列表"""
        return [img["url"] for img in self.pics] if self.pics else []

    def is_visible(self) -> bool:
        """检查微博是否可见"""
        return self.visible.get("type", 0) == 0

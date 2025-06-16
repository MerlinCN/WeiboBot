from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from WeiboBot.model.user import User

class Comment(BaseModel):
    """评论模型"""

    id: int = Field(description="评论ID")
    mid: str = Field(description="评论MID")
    created_at: str = Field(description="评论创建时间")
    text: str = Field(description="评论内容")
    source: str = Field(description="评论来源")
    reply_id: Optional[int] = Field(None, description="回复的评论ID")
    reply_text: Optional[str] = Field(None, description="回复的评论内容")
    pics: Optional[List[str]] = Field(None, description="评论图片列表")
    like_counts: int = Field(0, description="点赞数")
    is_liked: bool = Field(False, description="是否已点赞")
    is_followed: bool = Field(False, description="是否已关注评论用户")
    user: "User" = Field(None, description="评论用户")
    comments: Union[List["Comment"], None,bool] = Field(None, description="子评论列表")
    class Config:
        extra = "ignore"

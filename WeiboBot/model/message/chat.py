from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from WeiboBot.typing import MID

if TYPE_CHECKING:
    from WeiboBot.model import User


class ChatUser(BaseModel):
    id: int = Field(description="用户ID/群ID")
    screen_name: str = Field(description="用户昵称/群昵称")
    avatar_large: str = Field(description="头像/群头像")
    remark: str = Field(description="备注")
    verified: bool = Field(description="是否认证")
    verified_type: int = Field(description="认证类型")
    verified_type_ext: int = Field(description="认证类型扩展")


class Chat(BaseModel):
    created_at: str = Field(description="创建时间")
    scheme: str = Field(description="详情url")
    unread: int = Field(description="未读消息数")
    text: str = Field(description="消息内容")
    user: ChatUser = Field(description="用户")

    class Config:
        extra = "ignore"


class Message(BaseModel):
    created_at: str = Field(description="创建时间")
    dm_type: int = Field(description="消息类型")
    id: str = Field(description="消息ID")
    media_type: int = Field(description="媒体类型")
    msg_status: int = Field(description="消息状态")
    recipient_id: int = Field(description="收件人ID")
    recipient_screen_name: str = Field(description="收件人的昵称")
    sender_id: int = Field(description="发送者ID")
    sender_screen_name: str = Field(description="发送者的昵称")
    text: str = Field(description="内容")
    attachment: Dict[str, Any] = Field(default=None, description="附件")

    class Config:
        extra = "ignore"


class ChatDetail(BaseModel):
    total_number: Optional[int] = Field(description="总数")
    following: Optional[bool] = Field(description="是否关注")
    last_read_mid: Optional[int] = Field(description="最后阅读的MID")
    title: str = Field(description="标题")
    users: Dict[MID, "User"] = Field(description="用户列表")
    msgs: List[Message] = Field(description="消息列表")

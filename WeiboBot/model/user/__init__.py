from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from WeiboBot.model.weibo import Weibo


class User(BaseModel):
    id: int = Field(description="用户id")
    screen_name: str = Field(description="用户昵称")
    profile_image_url: str = Field(description="用户头像")
    profile_url: str = Field(description="用户主页")
    statuses_count: int = Field(description="微博数")
    verified: bool = Field(description="是否是微博认证用户")
    verified_type: int = Field(description="认证类型")
    close_blue_v: bool = Field(description="是否关注微博蓝V")
    description: str = Field(description="用户描述")
    gender: str = Field(description="性别")
    mbtype: int = Field(description="会员类型")
    urank: int = Field(description="用户等级")
    mbrank: int = Field(description="会员等级")
    follow_me: int = Field(description="是否关注我")
    following: int = Field(description="我是否关注")
    follow_count: int = Field(description="关注数")
    followers_count: str = Field(description="粉丝数")
    followers_count_str: str = Field(description="粉丝数")
    cover_image_phone: str = Field(description="主页头图")
    avatar_hd: str = Field(description="高清头像")
    like: bool = Field(description="是否喜欢")
    like_me: bool = Field(description="是否喜欢我")
    badge: Optional[dict] = Field(default_factory=dict, description="徽章")
    verified_type_ext: Optional[int] = Field(default=None, description="认证类型扩展")
    verified_reason: str = Field(description="认证原因")
    statuses: Optional[List["Weibo"]] = Field(
        default_factory=list, description="最新微博"
    )

    class Config:
        extra = "ignore"

    def __str__(self) -> str:
        result = f"用户名:{self.screen_name},关注:{self.follow_count},粉丝:{self.followers_count},微博数量:{self.statuses_count}\n"
        result += f"微博简介:{self.description}\n"
        result += f"微博地址:{self.profile_url}\n"
        result += f"微博头像:{self.profile_image_url}\n"
        result += f"微博背景图:{self.cover_image_phone}\n"
        return result

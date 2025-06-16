from typing import TYPE_CHECKING, List

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .weibo import Weibo


class Page(BaseModel):
    max_id: int = Field(description="最大ID")
    interval: int = Field(description="间隔")
    since_id: int = Field(description="起始ID")
    statuses: List["Weibo"] = Field(description="微博列表")

from typing import TYPE_CHECKING, List

from pydantic import Field
from ..base import MetaBaseModel

if TYPE_CHECKING:
    from .weibo import Weibo


class Page(MetaBaseModel):
    max_id: int = Field(description="最大ID")
    interval: int = Field(description="间隔")
    since_id: int = Field(description="起始ID")
    statuses: List["Weibo"] = Field(description="微博列表")

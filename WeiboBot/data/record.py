from tortoise import fields, models


class WeiboRead(models.Model):
    id = fields.IntField(pk=True)
    mid = fields.IntField()

    class Meta:
        table = "weibo_read"

    @classmethod
    async def create_record(cls, mid: int) -> "WeiboRead":
        """创建一条微博阅读记录"""
        return await cls.create(mid=mid)

    @classmethod
    async def get_by_mid(cls, mid: int) -> "WeiboRead":
        """根据微博ID查询记录"""
        return await cls.filter(mid=mid).first()


class MentionCmtRead(models.Model):
    id = fields.IntField(pk=True)
    mid = fields.IntField()

    class Meta:
        table = "mention_cmt_read"

    @classmethod
    async def create_record(cls, mid: int) -> "MentionCmtRead":
        """创建一条@评论阅读记录"""
        return await cls.create(mid=mid)

    @classmethod
    async def get_by_mid(cls, mid: int) -> "MentionCmtRead":
        """根据@评论ID查询记录"""
        return await cls.filter(mid=mid).first()


class WeiboRepost(models.Model):
    id = fields.IntField(pk=True)
    mid = fields.IntField()

    class Meta:
        table = "weibo_repost"

    @classmethod
    async def create_record(cls, mid: int) -> "WeiboRepost":
        """创建一条微博转发记录"""
        return await cls.create(mid=mid)

    @classmethod
    async def get_by_mid(cls, mid: int) -> "WeiboRepost":
        """根据微博ID查询记录"""
        return await cls.filter(mid=mid).first()

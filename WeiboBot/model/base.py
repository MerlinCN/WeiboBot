from pydantic import BaseModel, Field


class MetaBaseModel(BaseModel):
    metadata: dict = Field(default_factory=dict, description="原始数据")

    @classmethod
    def model_validate(cls, data):
        obj = super().model_validate(data)
        obj.metadata = data
        return obj

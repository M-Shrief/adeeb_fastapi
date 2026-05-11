from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import general

NameField = Annotated[str, Field(max_length=256, examples=["محمود شاكر"])]
NameField_Optional =  Annotated[str | None, Field(default=None, max_length=256, examples=["محمود شاكر"])]
TimePeriodField = Annotated[general.TimePeriodEnum, Field(default=general.TimePeriodEnum.UNDEFINED)]
TimePeriodField_Optional = Annotated[general.TimePeriodEnum | None, Field(default=None)]
BioField = Annotated[str, Field(max_length=1024)]
BioField_Optional = Annotated[str | None, Field(default=None, max_length=1024)]

class FullSchema(BaseModel):
    id: general.IDField
    name: NameField
    time_period: TimePeriodField
    bio: BioField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class DescriptiveSchema(BaseModel):
    id: general.IDField
    name: NameField
    time_period: TimePeriodField
    bio: BioField
    reviewed: general.ReviewedField


class MinimalSchema(BaseModel):
    id: general.IDField
    name: NameField

from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import adeebs, general, api, poems, chosen_verses, prose_qoutes

class GetAdeeb_Res(adeebs.DescriptiveSchema):
    poems: list[poems.MinimalSchema]
    chosen_verses: list[chosen_verses.MinimalSchema]
    prose_qoutes: list[prose_qoutes.MinimalSchema]

class CreateOneAdeeb_Req(BaseModel):
    name: adeebs.NameField
    time_period: adeebs.TimePeriodField
    bio: adeebs.BioField
    reviewed: general.ReviewedField

class CreateOneAdeeb_Res(BaseModel):
    id: general.IDField
    name: adeebs.NameField
    time_period: adeebs.TimePeriodField
    bio: adeebs.BioField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class CreateManyAdeeb_Res(BaseModel):
    created_items: Annotated[list[CreateOneAdeeb_Res], Field(default=[])]
    invalid_items: Annotated[list[api.InvalidDataFieldType[CreateOneAdeeb_Req]], Field(default=[])]
    success_count: Annotated[int, Field(default=0)]

class UpdateAdeeb_Req(BaseModel):
    name: adeebs.NameField_Optional
    time_period: adeebs.TimePeriodField_Optional
    bio: adeebs.BioField_Optional
    reviewed: general.ReviewedField_Optional
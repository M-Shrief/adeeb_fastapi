
from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import poems, general, api

class GetPoem_Res(poems.DescriptiveSchema):
    pass

class CreateOnePoem_Req(BaseModel):
    adeeb_id: general.AdeebIDField
    intro: poems.IntroField
    verses: poems.VersesField
    is_couplet: poems.IsCoupletField
    reviewed: general.ReviewedField

class CreateOnePoem_Res(BaseModel):
    id: general.IDField
    adeeb_id: general.AdeebIDField
    intro: poems.IntroField
    verses: poems.VersesField
    is_couplet: poems.IsCoupletField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class CreateManyPoem_Res(BaseModel):
    created_items: Annotated[list[CreateOnePoem_Res], Field(default=[])]
    invalid_items: Annotated[list[api.InvalidDataFieldType[CreateOnePoem_Req]], Field(default=[])]
    success_count: Annotated[int, Field(default=0)]

class UpdatePoem_Req(BaseModel):
    adeeb_id: general.AdeebIDField_Optional
    intro: poems.IntroField_Optional
    verses: poems.VersesField_Optional
    is_couplet: poems.IsCoupletField_Optional
    reviewed: general.ReviewedField_Optional

from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import chosen_verses, general, api

class GetChosenVerses_Res(chosen_verses.DescriptiveSchema):
    pass

class CreateOneChosenVerses_Req(BaseModel):
    adeeb_id: general.AdeebIDField
    poem_id: general.PoemIDField
    tags: general.TagsField
    verses: general.VersesField
    is_couplet: general.IsCoupletField
    reviewed: general.ReviewedField

class CreateOneChosenVerses_Res(BaseModel):
    id: general.IDField
    adeeb_id: general.AdeebIDField
    poem_id: general.PoemIDField
    tags: general.TagsField
    verses: general.VersesField
    is_couplet: general.IsCoupletField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class CreateManyChosenVerses_Res(BaseModel):
    created_items: Annotated[list[CreateOneChosenVerses_Res], Field(default=[])]
    invalid_items: Annotated[list[api.InvalidDataFieldType[CreateOneChosenVerses_Req]], Field(default=[])]
    success_count: Annotated[int, Field(default=0)]


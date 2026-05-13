from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import general


class FullSchema(BaseModel):
    id: general.IDField
    tags: general.TagsField
    verses: general.VersesField
    is_couplet: general.IsCoupletField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField
    # Relations
    adeeb_id: general.AdeebIDField
    poem_id: general.PoemIDField

class DescriptiveSchema(BaseModel):
    id: general.IDField
    tags: general.TagsField
    verses: general.VersesField
    is_couplet: general.IsCoupletField
    reviewed: general.ReviewedField
    # Relations
    adeeb_id: general.AdeebIDField
    poem_id: general.PoemIDField

class MinimalSchema(BaseModel):
    id: general.IDField
    verses: general.VersesField

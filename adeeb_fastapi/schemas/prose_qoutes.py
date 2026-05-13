from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import general

QouteField = Annotated[str, Field(max_length=512)]
QouteField_Optional =  Annotated[str | None, Field(default=None, max_length=512)]

SourceField = Annotated[str | None, Field(default=None, max_length=256)]

class FullSchema(BaseModel):
    id: general.IDField
    tags: general.TagsField
    qoute: QouteField
    source: SourceField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField
    # Relations
    adeeb_id: general.AdeebIDField

class DescriptiveSchema(BaseModel):
    id: general.IDField
    tags: general.TagsField
    qoute: QouteField
    source: SourceField
    reviewed: general.ReviewedField
    # Relations
    adeeb_id: general.AdeebIDField

class MinimalSchema(BaseModel):
    id: general.IDField
    qoute: QouteField

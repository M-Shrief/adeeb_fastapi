
from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import prose_qoutes, general, api

class GetProseQoute_Res(prose_qoutes.DescriptiveSchema):
    pass

class CreateOneProseQoute_Req(BaseModel):
    adeeb_id: general.AdeebIDField
    tags: general.TagsField
    qoute: prose_qoutes.QouteField
    source: prose_qoutes.SourceField
    reviewed: general.ReviewedField

class CreateOneProseQoute_Res(BaseModel):
    id: general.IDField
    adeeb_id: general.AdeebIDField
    tags: general.TagsField
    qoute: prose_qoutes.QouteField
    source: prose_qoutes.SourceField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class CreateManyProseQoute_Res(BaseModel):
    created_items: Annotated[list[CreateOneProseQoute_Res], Field(default=[])]
    invalid_items: Annotated[list[api.InvalidDataFieldType[CreateOneProseQoute_Req]], Field(default=[])]
    success_count: Annotated[int, Field(default=0)]

class UpdateProseQoute_Req(BaseModel):
    adeeb_id: general.AdeebIDField_Optional
    tags: general.TagsField_Optional
    qoute: prose_qoutes.QouteField_Optional
    source: prose_qoutes.SourceField
    reviewed: general.ReviewedField_Optional

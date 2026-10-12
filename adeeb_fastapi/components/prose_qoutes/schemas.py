
from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import prose_qoutes, general, api, adeebs

class GetProseQoute_Res(prose_qoutes.DescriptiveSchema):
    adeeb: adeebs.MinimalSchema

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

class UpdateProseQoute_Req(BaseModel):
    adeeb_id: general.AdeebIDField_Optional
    tags: general.TagsField_Optional
    qoute: prose_qoutes.QouteField_Optional
    source: prose_qoutes.SourceField
    reviewed: general.ReviewedField_Optional

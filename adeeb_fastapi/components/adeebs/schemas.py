
from pydantic import BaseModel
###
from adeeb_fastapi.schemas import adeebs, general

class GetAdeeb_Res(adeebs.DescriptiveSchema):
    pass

class CreateOne_Req(BaseModel):
    name: adeebs.NameField
    time_period: adeebs.TimePeriodField
    bio: adeebs.BioField
    reviewed: general.ReviewedField

class CreateOne_Res(BaseModel):
    id: general.IDField
    name: adeebs.NameField
    time_period: adeebs.TimePeriodField
    bio: adeebs.BioField
    reviewed: general.ReviewedField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField
from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import general, users, jwt

class GetOne_Res_Body(jwt.DescriptiveSchema):
    user: users.DescriptiveSchema

class Refresh_Res_Body(BaseModel):
    access_token: Annotated[str, Field()]

class CreateOne_Req_Body(BaseModel):
    family_id: general.IDField
    used: jwt.UsedField_Optional
    is_banned: jwt.IsBannedField
    token_type: jwt.TokenTypeField
    exp: jwt.EXPField
    iat: jwt.IATField
    # Relations
    user_id: general.UserIDField


class UpdateOne_Req_Body(BaseModel):
    family_id: general.IDField_Optional
    used: jwt.UsedField_Optional
    is_banned: jwt.IsBannedField_Optional
    token_type: jwt.TokenTypeField_Optional
    exp: jwt.EXPField_Optional
    iat: jwt.IATField_Optional
    # Relations
    user_id: general.UserIDField_Optional

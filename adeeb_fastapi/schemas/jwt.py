from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime
from enum import Enum
###
from adeeb_fastapi.schemas import general, users 

UsedField = Annotated[bool, Field(default=False)]
UsedField_Optional = Annotated[bool  | None, Field(default=None)]

IsBannedField = Annotated[bool, Field(default=False)]
IsBannedField_Optional = Annotated[bool  | None, Field(default=None)]

EXPField=   Annotated[datetime, Field()]
EXPField_Optional=   Annotated[datetime | None, Field(default=None)]

IATField=   Annotated[datetime, Field()]
IATField_Optional=   Annotated[datetime | None, Field(default=None)]

class TokenTypeEnum(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

TokenTypeField=   Annotated[TokenTypeEnum, Field()]
TokenTypeField_Optional=   Annotated[TokenTypeEnum | None, Field(default=None)]

class FullSchema(BaseModel):
    jti: general.IDField
    family_id: general.IDField
    used: UsedField_Optional
    is_banned: IsBannedField
    token_type: TokenTypeField
    exp: EXPField
    iat: IATField
    # Relations
    user_id: general.UserIDField

class DescriptiveSchema(FullSchema):
    pass

class MinimalSchema(BaseModel):
    jti: general.IDField
    family_id: general.IDField
    is_banned: IsBannedField_Optional
    # Relations
    user_id: general.UserIDField

from pydantic import BaseModel, Field
from enum import Enum
from typing import Annotated
###
from adeeb_fastapi.schemas import general

UsernameField = Annotated[str, Field(max_length=256)]
UsernameField_Optional =  Annotated[str | None, Field(default=None, max_length=256)]

PasswordField = Annotated[str, Field(min_length=8, max_length=256)]
PasswordField_Optional = Annotated[str | None, Field(default=None, min_length=8, max_length=256)]

class RoleEnum(str, Enum):
    BANNED = "Banned"
    Normal = "Normal"
    DBA = 'DBA'
    Analytics = 'Analytics'
    Management = 'Management'

RolesField = Annotated[list[RoleEnum], Field(default=[RoleEnum.Normal], min_length=1)]
RolesField_Optional = Annotated[list[RoleEnum] | None, Field(default=None, min_length=1)]

class FullSchema(BaseModel):
    id: general.IDField
    username: UsernameField
    password: PasswordField
    roles: RolesField
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField

class DescriptiveSchema(BaseModel):
    id: general.IDField
    username: UsernameField
    roles: RolesField


class MinimalSchema(BaseModel):
    id: general.IDField
    username: UsernameField

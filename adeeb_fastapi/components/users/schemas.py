
from pydantic import BaseModel, Field
from typing import Annotated
###
from adeeb_fastapi.schemas import users, general, api

class GetUser_Res(users.DescriptiveSchema):
    pass

class UserSignup_Req(BaseModel):
    username: users.UsernameField
    password: users.PasswordField
    roles : users.RolesField

class UserLogin_Req(BaseModel):
    username: users.UsernameField
    password: users.PasswordField

class UserAuth_Res(BaseModel):
    """Schema used as a response for a user's signup or login"""
    user: users.DescriptiveSchema   
    access_token: str 

class UpdateCurrentUser_Req(BaseModel):
    """Used in PUT /users/me

    we don't allow updating user.roles deny normal users from upgrading their roles.
    """
    username: users.UsernameField_Optional
    password: users.PasswordField_Optional


class UpdateUserById_Req(BaseModel):
    f"""Used in PUT /users/{id}

    for upper users like DBA, Management, Analytics...etc
    """
    username: users.UsernameField_Optional
    password: users.PasswordField_Optional
    roles : users.RolesField_Optional


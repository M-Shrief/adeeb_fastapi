
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

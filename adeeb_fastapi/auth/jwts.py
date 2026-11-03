"""JWT related functionalities"""
import jwt
from typing import Literal
from pydantic import ValidationError
### 
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.config import access_jwt_config, refresh_jwt_config
from adeeb_fastapi.schemas import jwt as jwt_schemas
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.database.models import JWT as JWTModel
from adeeb_fastapi.auth import errors

# claims.permissions
WRITE_PERM = ":write"  # write permission  
READ_PERM = ":read" # read permission

def create_permissions(roles: list[RoleEnum])->list[str]:
    permission: list[str] = []
    for role in roles:
        permission.append(role + WRITE_PERM)
        permission.append(role + READ_PERM)

    return permission

def create_authorized_item(role: RoleEnum, op: Literal["read", "write"]):
    if op == "write":
        return role + WRITE_PERM
    else:
        return role + READ_PERM

def check_permission(authorized_list: list[str], permissions: list[str], op: Literal["read", "write"]):
    isAuthorized: bool = False
    is_banned = False

    for perm in permissions:
        if op == "write" and perm == RoleEnum.Banned + WRITE_PERM:
            is_banned = True
            break
        elif op == "read" and perm == RoleEnum.Banned + READ_PERM:
            is_banned = True
            break
        else:
            try:
                _ = authorized_list.index(perm)
                # if it didn't raise an error:
                isAuthorized = True
            except ValueError:
                continue
    
    if is_banned:
        isAuthorized= False

    return isAuthorized

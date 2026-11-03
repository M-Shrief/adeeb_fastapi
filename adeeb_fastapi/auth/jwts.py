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

# Access & Refresh tokens exp field in minutes
ACCESS_EXP_IN_MIN = 15
REFRESH_EXP_IN_MIN = 60 * 24 * 7

def new_claims(user: jwt_schemas.Claims_User, model: JWTModel | None = None, schema: jwt_schemas.DescriptiveSchema | None = None, token_type: Literal["access", "refresh"] = "access"):
    permissions = create_permissions(user.roles)

    if model is not None:
        exp= int(model.exp.timestamp())
        iat= int(model.iat.timestamp())

        if token_type == "access":
            return jwt_schemas.Claims(
                jti=model.jti,
                user=user,
                family_id=model.family_id,
                permissions=permissions,
                token_type=model.token_type,
                exp=exp,
                iat=iat,
            )
        else:
            return jwt_schemas.Claims(
                jti=model.jti,
                user=None,
                family_id=model.family_id,
                permissions=None,
                token_type=model.token_type,
                exp=exp,
                iat=iat,
            )

    elif schema is not None:
        exp= int(schema.exp.timestamp())
        iat= int(schema.iat.timestamp())
        if token_type == "access":
            return jwt_schemas.Claims(
                jti=schema.jti,
                user=user,
                family_id=schema.family_id,
                permissions=permissions,
                token_type=schema.token_type,
                exp=exp,
                iat=exp,
            )
        else:
            return jwt_schemas.Claims(
                jti=schema.jti,
                user=None,
                family_id=schema.family_id,
                permissions=None,
                token_type=schema.token_type,
                exp=exp,
                iat=iat,
            )

    else:
        return None

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

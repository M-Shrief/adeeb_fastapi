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



async def create_jwt(claims: jwt_schemas.Claims)->str:
    if claims.token_type == "access":
        token = jwt.encode(
            payload=claims.model_dump(mode="json"),
            key=access_jwt_config.private_key,
            algorithm="RS256"
        )
    else: 
        token = jwt.encode(
            payload=claims.model_dump(mode="json",exclude_none= True),
            key=refresh_jwt_config.private_key,
            algorithm="RS256"
            )

    return token

async def verify_jwt(token: str, token_type: jwt_schemas.TokenTypeEnum = jwt_schemas.TokenTypeEnum.ACCESS) -> tuple[jwt_schemas.Claims, None] | tuple[None, errors.AuthError_ReasonEnum]:
    """Verify JWT token with secret public key, also verifiy token claims like exp, iat...etc.

    Note: it doesn't validate Token's permissions/roles for the request.
    """
    try:
        # Decode JWT token
        if token_type == jwt_schemas.TokenTypeEnum.ACCESS: 
            payload = jwt.decode(
                jwt=token,
                key=access_jwt_config.public_key,
                algorithms=["RS256"],
            )
        else:
            payload = jwt.decode(
                jwt=token,
                key=refresh_jwt_config.public_key,
                algorithms=["RS256"],
            )

        # return payload, True

        claims = jwt_schemas.Claims.model_validate(payload, extra="ignore")
        return claims, None

    except ValidationError:
        return None, errors.AuthError_ReasonEnum.INVALID_CLAIMS
    except jwt.exceptions.ExpiredSignatureError:
        return None, errors.AuthError_ReasonEnum.EXPIRED
    except jwt.exceptions.ImmatureSignatureError:
        return None, errors.AuthError_ReasonEnum.IMMATURE
    except jwt.exceptions.InvalidTokenError as e: # that's the base error for decode()
        logger.error("Unknown error verifing JWT token", error=e)
        return None, errors.AuthError_ReasonEnum.INVALID_TOKEN

# Access & Refresh tokens exp field in minutes
ACCESS_EXP_IN_MIN = 15
REFRESH_EXP_IN_MIN = 60 * 24 * 7

async def new_claims(user: jwt_schemas.Claims_User, model: JWTModel | None = None, schema: jwt_schemas.DescriptiveSchema | None = None):
    permissions = await create_permissions(user.roles)

    if model is not None:
        exp= int(model.exp.timestamp())
        iat= int(model.iat.timestamp())

        if model.token_type == jwt_schemas.TokenTypeEnum.ACCESS:
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
        if schema.token_type == jwt_schemas.TokenTypeEnum.ACCESS:
            return jwt_schemas.Claims(
                jti=schema.jti,
                user=user,
                family_id=schema.family_id,
                permissions=permissions,
                token_type=schema.token_type,
                exp=exp,
                iat=iat,
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


type OP = Literal['write', 'read']
# claims.permissions
WRITE_PERM = ":write"  # write permission  
READ_PERM = ":read" # read permission

async def create_permissions(roles: list[RoleEnum])->list[str]:
    permission: list[str] = []
    for role in roles:
        permission.append(role + WRITE_PERM)
        permission.append(role + READ_PERM)

    return permission

def create_authorized_item(role: RoleEnum, op: OP):
    if op == "write":
        return role + WRITE_PERM
    else:
        return role + READ_PERM

async def check_permission(authorized_list: list[str], permissions: list[str], op: OP):
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

async def check_if_banned(permissions: list[str], op: OP):
    is_banned = False

    for perm in permissions:
        if op == "write" and perm == RoleEnum.Banned + WRITE_PERM:
            is_banned = True
            break
        elif op == "read" and perm == RoleEnum.Banned + READ_PERM:
            is_banned = True
            break
        else:
            continue
    
    return is_banned

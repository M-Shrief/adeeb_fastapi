from fastapi import HTTPException, status, Depends, Request, Header
import bcrypt
import jwt
from uuid import UUID
from typing import Literal, Annotated
from datetime import UTC, datetime, timedelta
### 
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.config import jwt_config
from adeeb_fastapi.schemas.users import RoleEnum

AuthorizationError = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

def create_jwt(id: UUID, username: str, roles: list[RoleEnum])->str:
    payload = create_jwt_payload(id, username, roles)
    token: str = jwt.encode(
        payload=payload,
        key=jwt_config.private_key,
        algorithm="RS256"
        )

    return token

def verify_jwt(authorization_header: str):
    """Verify JWT token with secret public key, also verifiy expirate date.
    
    Note: it doesn't validate permissions, as it'll give false negatives will be thought it's because of permissions but it's because token validity or expiration date.
    """
    token = authorization_header[7:] # Removes: "Bearer "
    try:
        # Decode JWT token
        payload = jwt.decode(
            jwt=token,
            key=jwt_config.public_key,
            algorithms=["RS256"]
            )

        # Check expiration date
        exp = payload.get("exp")
        if exp is None:
            return payload, False
        expire_timepstamp = datetime.fromtimestamp(exp).replace(tzinfo=None)
        current_timepstamp = datetime.now(UTC).replace(tzinfo=None)
        # if the expire date is smaller than the current time (i.e. has passed), then it's not authorized 
        if expire_timepstamp < current_timepstamp:
            return payload, False

        return payload, True
    except jwt.DecodeError:
        return None, False

#  No need for a Payload TypedDict as I will only use it once.
def create_jwt_payload(id: UUID, username: str, roles: list[RoleEnum]):
    time: datetime = datetime.now(UTC).replace(tzinfo=None)

    payload= {
        "user": {
            "id": str(id),
            "username":username
        },
        "permissions": create_permissions(roles),
        "iat":time,
        "exp":time + timedelta(minutes= 60 * 2) # Expire after 2 hours
    }

    return payload


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
        if op == "write" and perm == RoleEnum.BANNED + WRITE_PERM:
            is_banned = True
            break
        elif op == "read" and perm == RoleEnum.BANNED + READ_PERM:
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

def hash_password(password: str) -> str:
    hashed_password: bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    return hashed_password.decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

async def write_ops_auth(request: Request):
    """Global router dependency that require JWT authorization in write operations.
    
    Require the user to be: Management, Analytics or DBA.
    """
    try:
        # Only process write operations
        if request.method in ["PUT", "POST", "PATCH", "DELETE"]:
        
            auth_header = request.headers.get("Authorization")
            if auth_header is None:
                raise AuthorizationError
            
            payload, verified = verify_jwt(auth_header)
            if verified is False or  payload is None:
                raise AuthorizationError

            permissions: list[str] | None = payload.get("permissions")
            if permissions is None:
                raise AuthorizationError

            authorized_list=[
                create_authorized_item(RoleEnum.Analytics, "write"),
                create_authorized_item(RoleEnum.DBA, "write"),
                create_authorized_item(RoleEnum.Management, "write"),
            ]

            is_administrator = check_permission(authorized_list, permissions, "write")
            if is_administrator is False: # if it's not admin
                raise AuthorizationError

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when checking authorization before write operation", request_url=request.url ,error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

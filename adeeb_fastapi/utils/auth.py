import bcrypt
import jwt
from uuid import UUID
from typing import Literal
from datetime import UTC, datetime, timedelta
### 
from adeeb_fastapi.config import JWTKeys
from adeeb_fastapi.schemas.users import RoleEnum


def create_jwt(id: UUID, username: str, roles: list[RoleEnum])->str:
    payload = create_jwt_payload(id, username, roles)
    token: str = jwt.encode(
        payload=payload,
        key=JWTKeys.get("private"),
        algorithm="RS256"
        )

    return token

def verify_jwt(authorization_header: str, authorized_list: list[str], op: Literal["read", "write"]):
    token = authorization_header[7:] # Removes: "Bearer "
    try:
        # Decode JWT token
        payload = jwt.decode(
            jwt=token,
            key=JWTKeys.get("public"),
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

        # Check permissions
        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            return payload, False



        isAuthorized= is_authorized(authorized_list=authorized_list, permissions=permissions, op=op)
        if isAuthorized is False:
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

def is_authorized(authorized_list: list[str], permissions: list[str], op: Literal["read", "write"]):
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

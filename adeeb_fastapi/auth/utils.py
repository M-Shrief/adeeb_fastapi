from fastapi import HTTPException, status, Request, Header, Response
from uuid import UUID
from typing import Literal, Annotated
### 
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas.jwt import Claims
from adeeb_fastapi.auth import jwts, errors


def check_adminstration(permissions: list[str], op: Literal["write", "read"]):
    authorized_list=[
        jwts.create_authorized_item(RoleEnum.Analytics, op),
        jwts.create_authorized_item(RoleEnum.DBA, op),
        jwts.create_authorized_item(RoleEnum.Management, op),
    ]
    is_administrator = jwts.check_permission(authorized_list, permissions, op)
    
    return is_administrator

def check_item_ownership(item_owner_id: UUID | None, claims: Claims):
    # if there's no user_id, then it's not a registered user, so no need to compare ids
    # Also we want to pass the model's field directly
    if item_owner_id is None or claims.user is None:
        return False
    elif item_owner_id != claims.user.id:
        return False
    else: # if it's owned by the user
        return True

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

async def write_ops_auth(request: Request, Authorization: Annotated[str | None, Header()] = None):
    """Require JWT authorization in write operations: POST - PUT - PATCH - DELETE
    
    Require the user to be: Management, Analytics or DBA.
    """
    try:
        # Only process write operations
        if request.method in ["PUT", "POST", "PATCH", "DELETE"]:
        
            if Authorization is None:
                raise errors.AuthError(errors.AuthError_ReasonEnum.HEADER, caused_in="route")
            
            claims, error = jwts.verify_jwt(Authorization[7:])
            if error is not None or claims is None:
                raise errors.AuthError(errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="route")

            if claims.permissions is None:
                raise errors.AuthError(errors.AuthError_ReasonEnum.PERM, caused_in="route")

            is_administrator = check_adminstration(claims.permissions, "write")
            if is_administrator is False:
                raise errors.AuthError(errors.AuthError_ReasonEnum.PERM, caused_in="route")

    except errors.AuthError as e:
        return errors.new_auth_error_response(e)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when checking authorization before write operation", request_url=request.url ,error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


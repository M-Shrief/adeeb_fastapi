from fastapi import HTTPException, status, Request, Header, Response
from uuid import UUID
from typing import Literal, Annotated
### 
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas.jwt import Claims
from adeeb_fastapi.auth import jwts, errors


def set_refresh_token_cookie(response: Response, refresh_token: str):
    """helper function to set refresh_token as a secure cookie to FastAPI response model"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,       # Prevents JavaScript access (XSS protection)
        secure=True,         # Only sent over HTTPS
        samesite="strict",   # Prevents CSRF attacks
        max_age=60 * jwts.REFRESH_EXP_IN_MIN      # 1 weeks (in seconds)
    )

def check_admin_permissions(permissions: list[str], op: Literal["write", "read"]):
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
                raise errors.AuthError(reason=errors.AuthError_ReasonEnum.HEADER, caused_in="middleware")
            
            claims, error = jwts.verify_jwt(Authorization[7:])
            if error is not None or claims is None:
                raise errors.AuthError(reason=errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="middleware")

            if claims.permissions is None:
                raise errors.AuthError(reason=errors.AuthError_ReasonEnum.PERM, caused_in="middleware")

            is_administrator = check_admin_permissions(claims.permissions, "write")
            if is_administrator is False:
                raise errors.AuthError(reason=errors.AuthError_ReasonEnum.PERM, caused_in="middleware")

    except errors.AuthError as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when checking authorization before write operation", request_url=request.url ,error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


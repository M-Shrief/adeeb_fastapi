from fastapi import status
from fastapi.responses import JSONResponse
from enum import Enum
from typing import Literal, Annotated
from pydantic import BaseModel, Field
##
from adeeb_fastapi.utils.errors import APIError

class AuthError_ReasonEnum(str, Enum):
    # token-specific
    HEADER = "Authorization header doesn't exist"
    INVALID_TOKEN = "Token is invalid"
    INVALID_CLAIMS = "Token's claims are invalid."
    EXPIRED = "Token is expired"
    USED = "Refresh Token has already been used"
    BANNED = "Token has been banned"
    IMMATURE = "Token's claims are immature, not logical"
    UNKNOWN = "Unkown error, try logging in again."
    # user-specific
    PERM = "User doesn't have the required permission"

class AuthError(APIError):
    """Standardized Error for Authentication & Authorization"""
    def __init__(self, caused_in: Literal["repository", "service", "route"], reason: AuthError_ReasonEnum | None = None, message: str | None =None):
        self.message: str | None = message
        self.reason: AuthError_ReasonEnum | None = reason
        self.caused_in: Literal["repository", "service", "route"] = caused_in
        super().__init__(status.HTTP_401_UNAUTHORIZED, self.caused_in)

class AuthError_ResSchema(BaseModel):
    """pydantic model used to infer 401 responses schema"""
    detail: Annotated[str, Field(default="Not Authorized")]
    reason: Annotated[AuthError_ReasonEnum | None, Field(default=None)]

def new_auth_error_response(e: AuthError):
    """return FastAPI's JSONResponse with status=401, and extracts AuthError.reason into res.body"""
    content = AuthError_ResSchema(detail="Not Authorized", reason=e.reason).model_dump(mode="json", exclude_none=True)
    return JSONResponse(status_code=401,content=content)


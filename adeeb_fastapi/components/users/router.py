from fastapi import APIRouter, HTTPException, status, Depends, Header, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID
from glide import GlideClient
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.auth import errors as auth_errors, utils as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.cache.index import get_async_cache
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.components.users import schemas as component_schemas, service


router = APIRouter(tags=["Users"])

@router.post(
    "/users/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.UserAuth_Res,
    response_model_exclude_none=True
    )
async def signup(user: component_schemas.UserSignup_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], response: Response):
    try: 
        result, refresh_token = await service.signup(user, cache, db)
        _ = auth_utils.set_refresh_token_cookie(response, refresh_token)
        return result 

    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User does already exists")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /users/signup", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    "/users/login",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=component_schemas.UserAuth_Res,
    response_model_exclude_none=True
)
async def login(user: component_schemas.UserLogin_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], response: Response):
    try:
        result, refresh_token = await service.login(user, cache, db)
        _ = auth_utils.set_refresh_token_cookie(response, refresh_token)
        return result 

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /users/login", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


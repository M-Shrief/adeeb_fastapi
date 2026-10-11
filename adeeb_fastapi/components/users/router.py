from fastapi import APIRouter, HTTPException, status, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.components.users import schemas as component_schemas, service


router = APIRouter(tags=["Users"])

@router.get(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=api_schemas.GetAll_Res[component_schemas.GetUser_Res],
    response_model_exclude_none=True    
)
async def get_users(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.get_all(queries, Authorization, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /users", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.get(
    "/users/me",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.GetUser_Res,
    response_model_exclude_none=True    
)
async def get_current_user(db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.get_current_user(Authorization, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /users/me", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/users/{id}",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.GetUser_Res,
    response_model_exclude_none=True    
)
async def get_user_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.get_one_by_id(id, Authorization, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    "/users/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.UserAuth_Res,
    response_model_exclude_none=True
    )
async def signup(user: component_schemas.UserSignup_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: 
        result = await service.signup(user, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User does already exists")
            case status.HTTP_400_BAD_REQUEST:
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
async def login(user: component_schemas.UserLogin_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result = await service.login(user, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /users/login", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.put(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_current_user(data: component_schemas.UpdateCurrentUser_Req, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        await service.update_current_user(Authorization, data, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User does already exists")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /users/me", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/users/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_user_by_id(id: UUID, data: component_schemas.UpdateUserById_Req, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        await service.update_user_by_id(id, Authorization, data, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User does already exists")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /users/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/users/{id}/ban",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def ban_user_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
             raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")
        await service.ban_user_by_id(id, Authorization, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /users/{id}/ban", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_current_user(db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.delete_current_user(Authorization, db)
        return result 
    
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User does already exists")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /users/me", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/users/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")
        result = await service.delete_one(id, Authorization, db)
        return result 
    
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is referrenced in other tables")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /users/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

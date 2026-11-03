from fastapi import APIRouter, HTTPException, status, Depends, Query, Header, Cookie, Response
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
from adeeb_fastapi.schemas import jwt as jwt_schemas, api as api_schemas
from adeeb_fastapi.components.users.jwt import schemas as component_schemas, service


router = APIRouter(tags=["JWT"])


@router.get(
    "/jwts",
    description="Get JWTs metadata",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
    response_model=api_schemas.GetAll_Res[jwt_schemas.FullSchema],
    response_model_exclude_none=True,
)
async def get_jwts(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: #
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        response_result = await service.get_all(queries, Authorization[7:], db)

        return response_result
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.get(
    "/jwts/family/{family_id}",
    description="Get JWTs metadata belonging to one family",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
    response_model=api_schemas.GetAll_Res[jwt_schemas.FullSchema],
    response_model_exclude_none=True,
)
async def get_family_jwts(family_id: UUID, queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: #
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        response_result = await service.get_all(queries, Authorization[7:], db, family_id=family_id)

        return response_result
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.get(
    "/jwts/user/{user_id}",
    description="Get JWTs metadata belonging to one user",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
    response_model=api_schemas.GetAll_Res[jwt_schemas.FullSchema],
    response_model_exclude_none=True,
)
async def get_user_jwts(user_id: UUID, queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: #
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        response_result = await service.get_all(queries, Authorization[7:], db, user_id=user_id)

        return response_result
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/jwts/{id}",
    description="Get JWT metadata",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetOne_Res_Body,
    response_model_exclude_none=True
)
async def get_jwt_by_id(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        jwt = await service.get_one_by_id(id, Authorization[7:], cache, db)

        return jwt
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="jwt is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    "/jwts/refresh",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.Refresh_Res_Body,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
    response_model_exclude_none=True,
    description="rotate JWT",
)
async def refresh(cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], response: Response, refresh_token: Annotated[str | None, Cookie()] = None):
    try:
        if refresh_token is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")
        
        access_token, refresh_token = await service.refresh(refresh_token, cache, db)
        _ = auth_utils.set_refresh_token_cookie(response, refresh_token)

        return component_schemas.Refresh_Res_Body(access_token=access_token) 
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /jwts/refresh", error=e, caused_in="router")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/jwts/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Update JWT metadata",
)
async def update_jwt(id: UUID, data: component_schemas.UpdateOne_Req_Body, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.update_one(id, Authorization[7:], data, cache, db)

        return 
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="jwt already exists")
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="jwt is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT jwts/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.put(
    "/jwts/{id}/ban",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Ban JWT",
)
async def ban_one_by_id(id: UUID, data: component_schemas.UpdateOne_Req_Body, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.ban_one_by_id(id, Authorization[7:], cache, db)

        return 
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="jwt is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT jwts/{id}/ban", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.put(
    "/jwts/family/{family_id}/ban",
    description="Ban all JWT belonging to a certain framily",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
)
async def ban_family_jwts(family_id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)],db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: #
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.ban_jwts_with_filters(Authorization[7:], cache, db, family_id=family_id)

        return 
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/jwts/user/{user_id}/ban",
    description="Ban all JWT belonging to a certain user",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
)
async def ban_user_jwts(user_id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)],db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: #
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.ban_jwts_with_filters(Authorization[7:], cache, db, user_id=user_id)

        return 
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET jwts", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/jwts/cleanup",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Cleanup JWTs",
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
)
async def cleanup(cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.cleanup(Authorization[7:], cache, db)

        return
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE jwts/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")



@router.delete(
    "/jwts/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="delete JWT",
    responses={
        401: {"model": auth_errors.AuthError_ResSchema, "description": "Unauthorized"}
    },
)
async def delete_jwt(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.HEADER, caused_in="route")

        await service.delete_one(id, Authorization[7:], cache, db)

        return
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                return auth_errors.new_auth_error_response(auth_errors.AuthError(caused_in=e.caused_in))
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
            case _: 
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE jwts/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

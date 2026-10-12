from adeeb_fastapi.schemas.api import GetAll_Res

from adeeb_fastapi.components.orders.schemas import GetOrders_Res

from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
from glide import GlideClient
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Order as OrderModel, Print as PrintModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import get_async_cache, cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas.orders import OrderStatusEnum
from adeeb_fastapi.components.orders import schemas as component_schemas, service

router = APIRouter(tags=["Orders"])

@router.get(
    "/orders",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[component_schemas.GetOrders_Res],
    response_model_exclude_none=True,
)
async def get_orders(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
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
        logger.error("Error in GET /orders", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.get(
    "/orders/me",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[component_schemas.GetOrders_Res],
    response_model_exclude_none=True,
)
async def get_user_orders(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")
        
        result = await service.get_user_orders(queries, Authorization, db)
        return result 

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /orders/me", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/orders/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetOrder_Res,
    response_model_exclude_none=True
)
async def get_order_by_id(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.get_one_by_id(id, Authorization, cache, db)
        return result 

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order's not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /orders/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/orders",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneOrder_Res,
    response_model_exclude_none=True
)
async def create_one_order(data: component_schemas.CreateOneOrder_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result = await service.create_one_order(data, db)
        return result 

    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /orders", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/orders/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyOrder_Res,
    response_model_exclude_none=True
)
async def create_many_orders(data: list[component_schemas.CreateOneOrder_Req], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")
        
        result = await service.create_many_orders(Authorization, data, db)
        return result 

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /orders/many", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    "/orders/{order_id}/prints/",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.PrintItem_Res,
    response_model_exclude_none=True
)
async def add_one_print(order_id: UUID, data: component_schemas.PrintItem_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.add_one_print(order_id, Authorization, data, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /orders/{id}/prints", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    "/orders/{order_id}/prints/many/",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.PrintItem_Res,
    response_model_exclude_none=True
)
async def add_many_prints(order_id: UUID, data: list[component_schemas.PrintItem_Req], cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.add_many_print(order_id, Authorization, data, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /orders/{id}/prints/many", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.put(
    "/orders/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_order(id: UUID, data: component_schemas.UpdateOrder_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.update_order(id, Authorization, data, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /orders/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/orders/{order_id}/prints/{print_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_print(order_id: UUID, print_id: UUID, data: component_schemas.UpdatePrint_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.update_print(order_id, print_id, Authorization, data, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /orders/{order_id}/prints/{print_id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/orders/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_order(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.delete_order(id, Authorization, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is referenced in other tabels")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /orders/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/orders/{order_id}/prints/{print_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_print(order_id: UUID, print_id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="route")

        result = await service.delete_print(order_id, print_id, Authorization, cache, db)
        return result

    except APIError as e:
        match e.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                raise auth_utils.AuthorizationError
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Print is referenced in other tabels")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /orders/{order_id}/prints/{print_id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

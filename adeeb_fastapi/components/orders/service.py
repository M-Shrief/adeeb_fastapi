from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from glide import GlideClient
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.schemas import api as api_schemas, orders as orders_schemas, users as users_schemas
from adeeb_fastapi.components.orders import repository, schemas as component_schemas

async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "read")
        if is_administrator is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result: api_schemas.GetAll_Res[component_schemas.GetOrders_Res] = await repository.get_all(queries, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_user_orders(queries: api_schemas.SharedQueriesForGetManyRequests, Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Normal, "read"),
        ]

        is_permitted = auth_utils.check_permission(authorized_list, permissions, "read")
        if is_permitted is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        user = payload["user"]
        id = user["id"]
        result = await repository.get_user_orders(id, queries, db)
        return result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders/me")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def get_one_by_id(id: UUID, Authorization: str, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "read")
        if is_administrator is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.get_one_by_id(id, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_one_order(data: component_schemas.CreateOneOrder_Req, db: AsyncSession):
    try:
        repo_result = await repository.create_one_order(data, db)
        return repo_result

    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_many_orders(Authorization: str, data: list[component_schemas.CreateOneOrder_Req], db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "read")
        if is_administrator is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.create_many_orders(data, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/many")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def add_one_print(order_id: UUID, Authorization: str, data: component_schemas.PrintItem_Req, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.add_one_print(order_id, order.user_id, data, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/{id}/prints")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def add_many_print(order_id: UUID, Authorization: str, data: list[component_schemas.PrintItem_Req], cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.add_many_print(order_id, order.user_id, data, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/{id}/prints/many")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_order(id: UUID, Authorization: str, data: component_schemas.UpdateOrder_Req, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.update_order(id, order, data, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in PUT /orders/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_print(order_id: UUID, print_id: UUID, Authorization: str, data: component_schemas.UpdatePrint_Req, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.update_print(order_id, print_id, data, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in PUT /orders/{order_id}/prints/{order_id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_order(id: UUID, Authorization: str, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.delete_order(id, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in DELETE /orders/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_print(order_id: UUID, print_id: UUID, Authorization: str, cache: GlideClient, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = auth_utils.check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")
            if order.is_updateable is False:
                raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.delete_print(order_id, print_id, cache, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in DELETE /orders/{order_id}/prints/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

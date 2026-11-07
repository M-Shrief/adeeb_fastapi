from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from glide import GlideClient
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.auth import jwts, errors as auth_errors, utils as auth_utils
from adeeb_fastapi.schemas import api as api_schemas, users as users_schemas
from adeeb_fastapi.components.orders import repository, schemas as component_schemas

async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, token: str, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "read", "service")

        repo_result: api_schemas.GetAll_Res[component_schemas.GetOrders_Res] = await repository.get_all(queries, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_user_orders(queries: api_schemas.SharedQueriesForGetManyRequests, token: str, db: AsyncSession):
    try:
        claims = await auth_utils.verifying_normal_user(token, "read", "service")

        if claims.user is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_CLAIMS, caused_in="service")

        result = await repository.get_user_orders(str(claims.user.id), queries, db)
        return result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders/me")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def get_one_by_id(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "read")
        if is_administrator is False:
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "read")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        return order

    except auth_errors.AuthError as e:
        raise e
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

async def create_many_orders(token: str, data: list[component_schemas.CreateOneOrder_Req], db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        repo_result = await repository.create_many_orders(data, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/many")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def add_one_print(order_id: UUID, token: str, data: component_schemas.PrintItem_Req, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")


        repo_result = await repository.add_one_print(order_id, order.user_id, data, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/{id}/prints")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def add_many_print(order_id: UUID, token: str, data: list[component_schemas.PrintItem_Req], cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        repo_result = await repository.add_many_print(order_id, order.user_id, data, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in POST /orders/{id}/prints/many")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_order(id: UUID, token: str, data: component_schemas.UpdateOrder_Req, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

            #  if it's updated by the owner, then remove admin's related fields -- aka assign them to undefine.
            data.is_updateable = None
            data.status = None
            data.reviewed = None
            data.user_id = None


        repo_result = await repository.update_order(id, order, data, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in PUT /orders/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_print(order_id: UUID, print_id: UUID, token: str, data: component_schemas.UpdatePrint_Req, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        repo_result = await repository.update_print(order_id, print_id, data, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in PUT /orders/{order_id}/prints/{order_id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_order(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        repo_result = await repository.delete_order(id, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in DELETE /orders/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_print(order_id: UUID, print_id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = await jwts.verify_jwt(token)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        if claims.permissions is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        order = await repository.get_one_by_id(order_id, cache, db)

        is_administrator = await auth_utils.check_admin_permissions(claims.permissions, "write")
        if is_administrator is False:
            if order.is_updateable is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_owner = await auth_utils.check_item_ownership(order.user_id, claims)
            if is_owner is False:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")
            is_banned = await jwts.check_if_banned(claims.permissions, "write")
            if is_banned:
                raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.PERM, caused_in="service")

        repo_result = await repository.delete_print(order_id, print_id, cache, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in DELETE /orders/{order_id}/prints/{id}")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

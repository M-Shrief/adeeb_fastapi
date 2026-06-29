from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
from glide import GlideClient
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Order as OrderModel, Print as PrintModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import get_async_cache, cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas.orders import OrderStatusEnum
from adeeb_fastapi.components.orders import schemas as component_schemas
from adeeb_fastapi.components.orders.shared import check_adminstration, check_order_ownership

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
            raise auth_utils.AuthorizationError
        
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        is_administrator = check_adminstration(permissions, "read")
        if is_administrator is False:
            raise auth_utils.AuthorizationError

        stmt = select(OrderModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)
        stmt = stmt.options(joins.prints_to_order)

        resp  = await db.execute(stmt)
        rows = resp.unique().all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        orders =  [component_schemas.GetOrders_Res.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[component_schemas.GetOrders_Res](data=orders, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when getting orders", error=e)
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
            raise auth_utils.AuthorizationError
        
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Normal, "read"),
        ]
        is_permitted = auth_utils.check_permission(authorized_list, permissions, "read")
        if is_permitted is False:
            raise auth_utils.AuthorizationError

        user = payload["user"]

        stmt = select(OrderModel, func.count().over().label('total')).where(OrderModel.user_id == user["id"]).offset(queries.offset).limit(queries.limit)
        stmt = stmt.options(joins.prints_to_order)

        resp  = await db.execute(stmt)
        rows = resp.unique().all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        orders =  [component_schemas.GetOrders_Res.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[component_schemas.GetOrders_Res](data=orders, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when getting orders", error=e)
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
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        cache_key = format_key_by_id("order", id)
        cache_res = await cache_get(cache_key, cache)

        if cache_res is not None:
            logger.info("cache")
            order = component_schemas.GetOrder_Res.model_validate(cache_res, from_attributes=True)
        else:
            stmt = select(OrderModel).where(OrderModel.id == id)
            stmt = stmt.options(joins.prints_to_order)
            res = await db.scalars(statement=stmt)
            order = res.unique().one()
            order = component_schemas.GetOrder_Res.model_validate(order, from_attributes=True)

        is_administrator = check_adminstration(permissions, "read")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order.id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError

        await cache_set(
            key=cache_key,
            value=order,
            client=cache
        )

        return order

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order is not found!")
    except Exception as e:
        logger.error("Error when getting a order by id", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/orders",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneOrder_Res,
    response_model_exclude_none=True
)
async def create_order(order_data: component_schemas.CreateOneOrder_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_order = OrderModel(
            name=order_data.name,
            phone=order_data.phone,
            address=order_data.address,
            reviewed=False,
            # delivery_schedule=order_data.delivery_schedule,
            is_updateable=True,
            status=OrderStatusEnum.IN_PROGRESS,
            user_id=order_data.user_id,
            prints=[] # early populate to prevent lazy-loading
        )
        db.add(new_order)
        await db.flush() # using flush to assign order.id without committing
        
        # update delivery_schedule to be 7 days after creation:
        new_order.delivery_schedule = new_order.created_at + component_schemas.DELIVERY_AFTER

        for print in order_data.prints:
            new_print = PrintModel(**print.model_dump(), order_id = new_order.id, user_id=order_data.user_id)
            db.add(new_print)
            await db.flush()
            new_order.prints.append(new_print)

        await db.commit()

        return new_order
    except Exception as e:
        logger.error("Error occurred while creating a order", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "order does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a order, try again later."
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail_msg)

@router.post(
    path="/orders/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyOrder_Res,
    response_model_exclude_none=True
)
async def create_orders(data: list[component_schemas.CreateOneOrder_Req], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError
        
        _, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False:
            raise auth_utils.AuthorizationError

        created_items: list[component_schemas.CreateOneOrder_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType[component_schemas.CreateOneOrder_Req]] = []

        for item in data:
            try:
                new_order = OrderModel(
                    name=item.name,
                    phone=item.phone,
                    address=item.address,
                    reviewed=False,
                    # delivery_schedule=item.delivery_schedule,
                    is_updateable=True,
                    status=OrderStatusEnum.IN_PROGRESS,
                    user_id=item.user_id,
                    prints=[] # early populate to prevent lazy-loading
                )
                db.add(new_order)
                await db.flush() # using flush to assign order.id without committing

                # update delivery_schedule to be 7 days after creation:
                new_order.delivery_schedule = new_order.created_at + component_schemas.DELIVERY_AFTER

                for print in item.prints:
                    new_print = PrintModel(**print.model_dump(), order_id = new_order.id)
                    db.add(new_print)        
                    await db.flush()
                    new_order.prints.append(new_print)

                await db.commit()

                created_items.append(component_schemas.CreateOneOrder_Res.model_validate(new_order, from_attributes=True))
            except Exception as e:
                logger.error("Error occurred while creating a order", error=e)
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "order does already exists"
                else:
                    msg = "An error occurred while creating a order, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType[component_schemas.CreateOneOrder_Req](
                    item=item,
                    message=msg
                    ))

        return component_schemas.CreateManyOrder_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        detail_msg = "An error occurred while creating many order entities, try again later."
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail_msg)

@router.post(
    "/orders/{order_id}/prints/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=component_schemas.PrintItem_Res,
    response_model_exclude_none=True
)
async def add_print(order_id: UUID, req_body: component_schemas.PrintItem_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        stmt = select(OrderModel).where(OrderModel.id == order_id)
        res = await db.scalars(statement=stmt)
        order = res.unique().one()

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]

        is_administrator = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError
            if order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unauthorized to be updated")

        new_print = PrintModel(**req_body.model_dump(), order_id=order.id, user_id=order.user_id)

        db.add(new_print)
        await db.commit()
        await db.refresh(new_print)

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])

        return new_print

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order is not found!")
    except Exception as e:
        logger.error("Error when getting a order by id", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/orders/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_order(id: UUID, req_body: component_schemas.UpdateOrder_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError


        stmt = select(OrderModel).where(OrderModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_order = res.unique().one()

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]

        is_administrator = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(existing_order.id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError

            if existing_order.is_updateable is False:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized to be updated")
            # Make sure the user can't update interanl values like: is_updateable, is_completed
            # we assign them to None, as we can exclude them later with model_dump(exclude_none=True)
            else: 
                req_body.is_updateable = None
                req_body.status = None

        # Ensuring Data Integrity
        ## If the order is aborted or marked as completed, then we make sure that is_updateable is False
        if req_body.status in [OrderStatusEnum.ABORTED, OrderStatusEnum.COMPLETED]:
            req_body.is_updateable = False
        elif req_body.status == OrderStatusEnum.IN_PROGRESS:
            req_body.is_updateable = True
        ## if it want to make is_updateable true, then we make sure status == "in progress".
        ## We don't need to worry about the user setting is_updateable to true, as we raise Auth error if it's false above
        elif req_body.is_updateable:
            req_body.status = OrderStatusEnum.IN_PROGRESS

        new_order_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_order_data.items():
            setattr(existing_order, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", id)
        _ = await cache.delete([cache_key])

        return api_schemas.Update_Res()

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order is not found!")
    except Exception as e:
        logger.error("Error when updating order", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/orders/{order_id}/prints/{print_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_print(order_id: UUID, print_id: UUID, req_body: component_schemas.UpdatePrint_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError
        
        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError

        order_stmt = select(OrderModel).where(OrderModel.id == order_id)
        res = await db.scalars(statement=order_stmt)
        order = res.unique().one()

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]

        is_administrator = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError
            # If the user wants to update it, we need to check if the order is updateable first.
            if order.is_updateable is False:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized to be updated")

        print_stmt = select(PrintModel).where(PrintModel.id == print_id)
        res = await db.scalars(statement=print_stmt)
        existing_print = res.unique().one()

        new_print_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body
        for key, value in new_print_data.items():
            setattr(existing_print, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])

        return api_schemas.Update_Res()

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order is not found!")
    except Exception as e:
        logger.error("Error when updating order", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/orders/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_order(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError


        order_stmt = select(OrderModel).where(OrderModel.id == id)
        res = await db.scalars(statement=order_stmt)
        order = res.unique().one()

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]

        is_administrator = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError
            if order.is_updateable is False:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")


        print_stmt = delete(PrintModel).where(PrintModel.order_id == id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        order_stmt = delete(OrderModel).where(OrderModel.id == id)
        _ = await db.execute(statement=order_stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", id)
        _ = await cache.delete([cache_key])

        return api_schemas.Delete_Res()

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order is not found!")
    except Exception as e:
        logger.error("Error when deleting order", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/orders/{order_id}/prints/{print_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_print(order_id: UUID, print_id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise auth_utils.AuthorizationError

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise auth_utils.AuthorizationError

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise auth_utils.AuthorizationError


        order_stmt = select(OrderModel).where(OrderModel.id == order_id)
        res = await db.scalars(statement=order_stmt)
        order = res.unique().one()


        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]

        is_administrator = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order.user_id, payload)
            if is_owner is False:
                raise auth_utils.AuthorizationError
            if order.is_updateable is False:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized to be updated")

        print_stmt = delete(PrintModel).where(PrintModel.id == print_id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])

        return api_schemas.Delete_Res()

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order is not found!")
    except Exception as e:
        logger.error("Error when deleting order", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

from fastapi import status
from glide import GlideClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.models import Order as OrderModel, Print as PrintModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import orders as orders_schemas, api as api_schemas
from adeeb_fastapi.components.orders import schemas as component_schemas




async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(OrderModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)
        stmt = stmt.options(joins.prints_to_order)

        resp  = await db.execute(stmt)
        rows = resp.unique().all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        orders =  [component_schemas.GetOrders_Res.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[component_schemas.GetOrders_Res](data=orders, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def get_user_orders(user_id: str, queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(OrderModel, func.count().over().label('total')).where(OrderModel.user_id == user_id).offset(queries.offset).limit(queries.limit)
        stmt = stmt.options(joins.prints_to_order)

        resp  = await db.execute(stmt)
        rows = resp.unique().all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        orders =  [component_schemas.GetOrders_Res.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[component_schemas.GetOrders_Res](data=orders, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /orders/me")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def get_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        cache_key = format_key_by_id("order", id)
        cache_res = await cache_get(cache_key, cache)

        if cache_res is not None:
            order = component_schemas.GetOrder_Res.model_validate(cache_res, from_attributes=True)
        else:
            stmt = select(OrderModel).where(OrderModel.id == id)
            stmt = stmt.options(joins.prints_to_order)
            res = await db.scalars(statement=stmt)
            order = res.unique().one()
            order = component_schemas.GetOrder_Res.model_validate(order, from_attributes=True)
            await cache_set(
                key=cache_key,
                value=order,
                client=cache
            )

        return order

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /orders/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def create_one_order(data: component_schemas.CreateOneOrder_Req, db: AsyncSession):
    try:
        new_order = OrderModel(
            name=data.name,
            phone=data.phone,
            address=data.address,
            reviewed=False,
            # delivery_schedule=data.delivery_schedule,
            is_updateable=True,
            status=orders_schemas.OrderStatusEnum.IN_PROGRESS,
            user_id=data.user_id,
            prints=[] # early populate to prevent lazy-loading
        )
        db.add(new_order)
        await db.flush() # using flush to assign order.id without committing
        
        # update delivery_schedule to be 7 days after creation:
        new_order.delivery_schedule = new_order.created_at + component_schemas.DELIVERY_AFTER

        for print in data.prints:
            new_print = PrintModel(**print.model_dump(), order_id = new_order.id, user_id=data.user_id)
            db.add(new_print)
            await db.flush()
            new_order.prints.append(new_print)

        await db.commit()

        return new_order

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in POST /orders", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def create_many_orders(data: list[component_schemas.CreateOneOrder_Req], db: AsyncSession):
    try:
        created_items: list[component_schemas.CreateOneOrder_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_order = OrderModel(
                    name=item.name,
                    phone=item.phone,
                    address=item.address,
                    reviewed=False,
                    # delivery_schedule=item.delivery_schedule,
                    is_updateable=True,
                    status=orders_schemas.OrderStatusEnum.IN_PROGRESS,
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
                await db.rollback()
                if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
                    msg = "foreign key error"
                else:
                    msg = "Unknown error, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType(
                    item_index=index,
                    message=msg
                    ))

        return api_schemas.CreateMany_Res[component_schemas.CreateOneOrder_Res](
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /orders/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def add_one_print(order_id: UUID, user_id: UUID | None, data: component_schemas.PrintItem_Req, cache: GlideClient, db: AsyncSession):
    try:
        new_print = PrintModel(**data.model_dump(), order_id=order_id, user_id=user_id)

        db.add(new_print)
        await db.commit()
        await db.refresh(new_print)

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])

        return new_print

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in POST /orders/{id}/prints", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def add_many_print(order_id: UUID, user_id: UUID | None, data: list[component_schemas.PrintItem_Req], cache: GlideClient, db: AsyncSession):
    try:
        created_items: list[component_schemas.PrintItem_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_print = PrintModel(**item.model_dump(), order_id=order_id, user_id=user_id)

                db.add(new_print)
                await db.commit()
                await db.refresh(new_print)

                created_items.append(component_schemas.PrintItem_Res.model_validate(new_print, from_attributes=True))
            except Exception as e:
                await db.rollback()
                if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
                    msg = "foreign key error"
                else:
                    msg = "Unknown error, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType(
                    item_index=index,
                    message=msg
                    ))

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])


        return api_schemas.CreateMany_Res[component_schemas.PrintItem_Res](
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /orders/{id}/prints/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def update_order(id: UUID, existing_order: component_schemas.GetOrder_Res, data: component_schemas.UpdateOrder_Req, cache: GlideClient, db: AsyncSession):
    try:
        # Ensuring Data Integrity
        ## If the order is aborted or marked as completed, then we make sure that is_updateable is False
        if data.status in [orders_schemas.OrderStatusEnum.ABORTED, orders_schemas.OrderStatusEnum.COMPLETED]:
            data.is_updateable = False
        elif data.status == orders_schemas.OrderStatusEnum.IN_PROGRESS:
            data.is_updateable = True
        ## if it want to make is_updateable true, then we make sure status == "in progress".
        ## We don't need to worry about the user setting is_updateable to true, as we raise Auth error if it's false above
        elif data.is_updateable:
            data.status = orders_schemas.OrderStatusEnum.IN_PROGRESS

        new_order_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_order_data.items():
            setattr(existing_order, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", id)
        _ = await cache.delete([cache_key])
 
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in PUT /orders/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def update_print(order_id: UUID, print_id: UUID, data: component_schemas.UpdatePrint_Req, cache: GlideClient, db: AsyncSession):
    try:

        print_stmt = select(PrintModel).where(PrintModel.id == print_id)
        res = await db.scalars(statement=print_stmt)
        existing_print = res.unique().one()

        new_print_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body
        for key, value in new_print_data.items():
            setattr(existing_print, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])
 
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in PUT /orders/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def delete_order(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        print_stmt = delete(PrintModel).where(PrintModel.order_id == id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        order_stmt = delete(OrderModel).where(OrderModel.id == id)
        _ = await db.execute(statement=order_stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", id)
        _ = await cache.delete([cache_key])
        
        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in DELETE /orders/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def delete_print(order_id: UUID, print_id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        print_stmt = delete(PrintModel).where(PrintModel.id == print_id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("order", order_id)
        _ = await cache.delete([cache_key])

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in DELETE /orders/{id}/prints/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

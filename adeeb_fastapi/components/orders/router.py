from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Order as OrderModel, Print as PrintModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.schemas.users import RoleEnum
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        is_administrator = check_adminstration(permissions, "read")
        if is_administrator is False:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

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
    "/orders/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetOrder_Res,
    response_model_exclude_none=True
)
async def get_order_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        stmt = select(OrderModel).where(OrderModel.id == id)
        stmt = stmt.options(joins.prints_to_order)
        res = await db.scalars(statement=stmt)
        order = res.unique().one()

        is_administrator = check_adminstration(permissions, "read")
        if is_administrator is False: # if it's not admin
            is_owner = check_order_ownership(order, payload)
            if is_owner is False:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

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
            is_aborted=False,
            is_completed=False,
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
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.post(
    path="/orders/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyOrder_Res,
    response_model_exclude_none=True
)
async def create_orders(data: list[component_schemas.CreateOneOrder_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
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
                    is_aborted=False,
                    is_completed=False,
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

    except Exception as e:
        detail_msg = "An error occurred while creating many order entities, try again later."
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.post(
    "/orders/{order_id}/prints/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=component_schemas.PrintItem_Res,
    response_model_exclude_none=True
)
async def add_print(order_id: UUID, req_body: component_schemas.PrintItem_Req, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

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
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
                # If the user wants to update it, we need to check if the order is updateable first.
                if order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")

        new_print = PrintModel(**req_body.model_dump(), order_id=order.id, user_id=order.user_id)

        db.add(new_print)
        await db.commit()
        await db.refresh(new_print)
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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_order(id: UUID, req_body: component_schemas.UpdateOrder_Req, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")


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
            if existing_order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(existing_order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
                # If the user wants to update it, we need to check if the order is updateable first.
                if existing_order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")
                # Make sure the user can't update interanl values like: is_updateable, is_completed
                # we assign them to None, as we can exclude them later with model_dump(exclude_none=True)
                else: 
                    req_body.is_updateable = None
                    req_body.is_completed = None

        # Ensuring Data Integrity
        ## request can't updated is_aborted & is_completed to be True, it's one or the other
        if req_body.is_aborted and req_body.is_completed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="request can't updated is_aborted & is_completed to be True, it's one or the other")
        ## If the order is aborted or marked as completed, then we make sure that is_updateable is False
        elif req_body.is_aborted or req_body.is_completed:
            req_body.is_updateable = False
        ## if it want to make is_updateable true, then we make user is_aborted & is_completed are false.
        ## We don't need to worry about the user setting it to true, as we raise Auth error if it's false above
        elif req_body.is_updateable:
            req_body.is_aborted = False
            req_body.is_completed = False

        new_order_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_order_data.items():
            setattr(existing_order, key, value)

        await db.commit()
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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_print(order_id: UUID, print_id: UUID, req_body: component_schemas.UpdatePrint_Req, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        
        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

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
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
                # If the user wants to update it, we need to check if the order is updateable first.
                if order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")

        print_stmt = select(PrintModel).where(PrintModel.id == print_id)
        res = await db.scalars(statement=print_stmt)
        existing_print = res.unique().one()

        new_print_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body
        for key, value in new_print_data.items():
            setattr(existing_print, key, value)

        await db.commit()
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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_order(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")


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
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
                # If the user wants to update it, we need to check if the order is updateable first.
                if order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")


        print_stmt = delete(PrintModel).where(PrintModel.order_id == id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        order_stmt = delete(OrderModel).where(OrderModel.id == id)
        _ = await db.execute(statement=order_stmt)
        await db.commit()

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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_print(order_id: UUID, print_id: UUID,db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try:
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")


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
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
                # If the user wants to update it, we need to check if the order is updateable first.
                if order.is_updateable is False:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Can't be updated")

        print_stmt = delete(PrintModel).where(PrintModel.id == print_id)
        _ = await db.execute(statement=print_stmt)
        await db.commit()

        return api_schemas.Delete_Res()

    except HTTPException as e:
        raise e
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order is not found!")
    except Exception as e:
        logger.error("Error when deleting order", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

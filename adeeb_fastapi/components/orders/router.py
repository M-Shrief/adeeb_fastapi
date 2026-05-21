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

router = APIRouter(tags=["Orders"])


# TODO: we make a function to handle Authorization,
# maybe make it return: {is_admin: bool, is_owner: bool, is_valid: bool}
# if is_valid=true one of the other is True, if it's false, both are false.
# if is_admin is true, we accept's it, if it's owner then we make further validations...etc

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
        
        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "read"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "read"),
            auth_utils.create_authorized_item(RoleEnum.Management, "read"),
        ]
        _, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="read")
        if verified is False:
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

        stmt = select(OrderModel).where(OrderModel.id == id)
        stmt = stmt.options(joins.prints_to_order)
        res = await db.scalars(statement=stmt)
        order = res.unique().one()

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "read"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "read"),
            auth_utils.create_authorized_item(RoleEnum.Management, "read"),
        ]
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="read")
        if payload is None: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        
        if verified is False: # if it's not admin
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: # check if it's the same user, if yes return order
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

        
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        res = await db.scalars(statement=stmt)
        order = res.unique().one()

        new_print = PrintModel(**req_body.model_dump(), order_id=order.id, user_id=order.user_id)

        authorized_list=[
            auth_utils.create_authorized_item(RoleEnum.Analytics, "write"),
            auth_utils.create_authorized_item(RoleEnum.DBA, "write"),
            auth_utils.create_authorized_item(RoleEnum.Management, "write"),
        ]
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="write")

        if payload is None: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
        
        if verified is False: # if it's not admin
            if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
            else:
                # check if it's the same user, if no raise Authorization error
                # if it's the same user, then we continue the request without raising errors
                user = payload["user"]
                if str(order.user_id) != user["id"]: 
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

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

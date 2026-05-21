from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Order as OrderModel, Print as PrintModel
from adeeb_fastapi.components.orders import schemas as component_schemas

router = APIRouter(tags=["Orders"])



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

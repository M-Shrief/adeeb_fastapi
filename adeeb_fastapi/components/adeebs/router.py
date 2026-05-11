from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Any, Literal
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Adeeb as AdeebModel
from adeeb_fastapi.schemas import adeebs as adeeb_schemas, api as api_schemas
from adeeb_fastapi.components.adeebs import schemas as component_schemas


router = APIRouter(tags=["Adeebs"])

@router.get(
    "/adeebs",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_adeebs(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(AdeebModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[1].total if rows else 0 # note: using 0 or 1 is the same, as count().over()...etc returns total_count with every row
        # We can get the data by: data = [row[0] for row in rows], 
        # but we merge fetching the data & validation in the same step.
        adeebs =  [adeeb_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema](data=adeebs, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting adeebs", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/adeebs",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOne_Res,
    response_model_exclude_none=True
)
async def create_adeeb(adeeb: component_schemas.CreateOne_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_adeeb = AdeebModel(**adeeb.model_dump())
        db.add(new_adeeb)
        await db.commit()
        await db.refresh(new_adeeb)

        return new_adeeb

    except Exception as e:
        logger.error("Error occurred while creating a adeeb", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "Category does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a adeeb, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import ChosenVerses as ChosenVersesModel
from adeeb_fastapi.schemas import chosen_verses as chosen_verses_schemas, api as api_schemas
from adeeb_fastapi.components.chosen_verses import schemas as component_schemas



router = APIRouter(tags=["ChosenVersess"])

@router.get(
    "/chosen_verses",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[chosen_verses_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_chosen_verses(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(ChosenVersesModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[1].total if rows else 0 
        chosen_verses =  [chosen_verses_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[chosen_verses_schemas.DescriptiveSchema](data=chosen_verses, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting chosen_verses", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/chosen_verses",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneChosenVerses_Res,
    response_model_exclude_none=True
)
async def create_one_chosen_verses(chosen_verses: component_schemas.CreateOneChosenVerses_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_chosen_verses = ChosenVersesModel(**chosen_verses.model_dump())
        db.add(new_chosen_verses)
        await db.commit()
        await db.refresh(new_chosen_verses)

        return new_chosen_verses

    except Exception as e:
        logger.error("Error occurred while creating a chosen_verses", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "chosen_verses does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a chosen_verses, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

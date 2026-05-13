from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import ProseQoute as ProseQouteModel
from adeeb_fastapi.schemas import prose_qoutes as prose_qoutes_schemas, api as api_schemas
from adeeb_fastapi.components.prose_qoutes import schemas as component_schemas



router = APIRouter(tags=["ProseQoutes"])

@router.get(
    "/prose_qoutes",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[prose_qoutes_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_prose_qoutes(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(ProseQouteModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[1].total if rows else 0 
        prose_qoutes =  [prose_qoutes_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[prose_qoutes_schemas.DescriptiveSchema](data=prose_qoutes, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting prose_qoutes", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/prose_qoutes",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneProseQoute_Res,
    response_model_exclude_none=True
)
async def create_prose_qoute(prose_qoute: component_schemas.CreateOneProseQoute_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_prose_qoute = ProseQouteModel(**prose_qoute.model_dump())
        db.add(new_prose_qoute)
        await db.commit()
        await db.refresh(new_prose_qoute)

        return new_prose_qoute

    except Exception as e:
        logger.error("Error occurred while creating a prose_qoute", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "prose_qoute does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a prose_qoute, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

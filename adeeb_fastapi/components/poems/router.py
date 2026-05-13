from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Poem as PoemModel
from adeeb_fastapi.schemas import poems as poems_schemas, api as api_schemas
from adeeb_fastapi.components.poems import schemas as component_schemas



router = APIRouter(tags=["Poems"])

@router.get(
    "/poems",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_poems(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(PoemModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[1].total if rows else 0 
        poems =  [poems_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema](data=poems, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting poems", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/poems",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOnePoem_Res,
    response_model_exclude_none=True
)
async def create_poem(poem: component_schemas.CreateOnePoem_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_poem = PoemModel(**poem.model_dump())
        db.add(new_poem)
        await db.commit()
        await db.refresh(new_poem)

        return new_poem

    except Exception as e:
        logger.error("Error occurred while creating a poem", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "poem does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a poem, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Adeeb as AdeebModel
from adeeb_fastapi.schemas import adeebs as adeeb_schemas
from adeeb_fastapi.components.adeebs import schemas as component_schemas


router = APIRouter(tags=["Adeebs"])

@router.get(
    "/adeebs",
    status_code=status.HTTP_200_OK,
    response_model=list[adeeb_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_adeebs(db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(AdeebModel)

        resp  = await db.scalars(stmt)
        adeebs = resp.all()

        return adeebs

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

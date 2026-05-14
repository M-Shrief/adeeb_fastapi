from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import ChosenVerses as ChosenVersesModel
from adeeb_fastapi.database import joins
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

@router.get(
    "/chosen_verses/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetChosenVerses_Res,
    response_model_exclude_none=True
)
async def get_chosen_verses_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(ChosenVersesModel).where(ChosenVersesModel.id == id)
        stmt = stmt.options(joins.adeebs_to_chosen_verses).options(joins.poems_to_chosen_verses)
        res = await db.scalars(statement=stmt)
        chosen_verses = res.unique().one()
        return chosen_verses

    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chosen_verses is not found!")
    except Exception as e:
        logger.error("Error when getting a chosen_verses by id", error=e)
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

@router.post(
    path="/chosen_verses/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyChosenVerses_Res,
    response_model_exclude_none=True
)
async def create_many_chosen_verses(data: list[component_schemas.CreateOneChosenVerses_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        created_items: list[component_schemas.CreateOneChosenVerses_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType[component_schemas.CreateOneChosenVerses_Req]] = []

        for item in data:
            try:
                new_chosen_verses = ChosenVersesModel(**item.model_dump())
                db.add(new_chosen_verses)
                await db.commit()
                await db.refresh(new_chosen_verses)

                created_items.append(component_schemas.CreateOneChosenVerses_Res.model_validate(new_chosen_verses, from_attributes=True))
            except Exception as e:
                logger.error("Error occurred while creating a chosen_verses", error=e)
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "chosen_verses does already exists"
                else:
                    msg = "An error occurred while creating a chosen_verses, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType[component_schemas.CreateOneChosenVerses_Req](
                    item=item,
                    message=msg
                    ))

        return component_schemas.CreateManyChosenVerses_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )


    except Exception as e:
        detail_msg = "An error occurred while creating many chosen_verses entities, try again later."
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.put(
    "/chosen_verses/{id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_chosen_verses(id: UUID, req_body: component_schemas.UpdateChosenVerses_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(ChosenVersesModel).where(ChosenVersesModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_chosen_verses = res.unique().one()

        new_chosen_verses_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_chosen_verses_data.items():
            setattr(existing_chosen_verses, key, value)

        await db.commit()
        return api_schemas.Update_Res()
        
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ChosenVerses is not found!")
    except Exception as e:
        logger.error("Error when updating chosen_verses", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/chosen_verses/{id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_chosen_verses(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = delete(ChosenVersesModel).where(ChosenVersesModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        return api_schemas.Delete_Res()
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ChosenVerses is not found!")
    except Exception as e:
        logger.error("Error when deleting chosen_verses", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.models import ChosenVerses as ChosenVersesModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.schemas import chosen_verses as chosen_verses_schemas, api as api_schemas
from adeeb_fastapi.components.chosen_verses import schemas as component_schemas




async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(ChosenVersesModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0 
        chosen_verses =  [chosen_verses_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[chosen_verses_schemas.DescriptiveSchema](data=chosen_verses, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /chosen_verses")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def get_one_by_id(id: UUID, db: AsyncSession):
    try:
        stmt = select(ChosenVersesModel).where(ChosenVersesModel.id == id)
        stmt = stmt.options(joins.adeebs_to_chosen_verses).options(joins.poems_to_chosen_verses)
        res = await db.scalars(statement=stmt)
        chosen_verses = res.unique().one()
        return chosen_verses
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /chosen_verses/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_one(chosen_verses: component_schemas.CreateOneChosenVerses_Req, db: AsyncSession):
    try:
        new_chosen_verses = ChosenVersesModel(**chosen_verses.model_dump())
        db.add(new_chosen_verses)
        await db.commit()
        await db.refresh(new_chosen_verses)

        return new_chosen_verses

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in POST /chosen_verses", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_many(data: list[component_schemas.CreateOneChosenVerses_Req], db: AsyncSession):
    try:
        created_items: list[component_schemas.CreateOneChosenVerses_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_chosen_verses = ChosenVersesModel(**item.model_dump())
                db.add(new_chosen_verses)
                await db.commit()
                await db.refresh(new_chosen_verses)

                created_items.append(component_schemas.CreateOneChosenVerses_Res.model_validate(new_chosen_verses, from_attributes=True))
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

        return component_schemas.CreateManyChosenVerses_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /chosen_verses/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_one(id: UUID, data: component_schemas.UpdateChosenVerses_Req, db: AsyncSession):
    try:
        stmt = select(ChosenVersesModel).where(ChosenVersesModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_chosen_verses = res.unique().one()

        new_chosen_verses_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_chosen_verses_data.items():
            setattr(existing_chosen_verses, key, value)

        await db.commit() 
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in PUT /chosen_verses/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_one(id: UUID, db: AsyncSession):
    try:
        stmt = delete(ChosenVersesModel).where(ChosenVersesModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in DELETE /chosen_verses/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

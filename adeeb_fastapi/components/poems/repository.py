from fastapi import status
from glide import GlideClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.models import Poem as PoemModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import poems as poems_schemas, api as api_schemas
from adeeb_fastapi.components.poems import schemas as component_schemas




async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(PoemModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        # We can get the data by: data = [row[0] for row in rows], 
        # but we merge fetching the data & validation in the same step.
        poems =  [poems_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema](data=poems, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /poems")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def get_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        cache_key = format_key_by_id("poem", id)
        cache_res = await cache_get(cache_key, cache)

        if cache_res is not None:
            poem = component_schemas.GetPoem_Res.model_validate(cache_res, from_attributes=True)
        else:
            stmt = select(PoemModel).where(PoemModel.id == id)
            stmt = stmt.options(joins.adeebs_to_poems).options(joins.chosen_verses_to_poem)
            res = await db.scalars(statement=stmt)
            poem = res.unique().one()

            poem = component_schemas.GetPoem_Res.model_validate(poem, from_attributes=True)
            
            await cache_set(
                    key=cache_key,
                    value=poem,
                    client=cache
                )

        return poem
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /poems/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_one(poem: component_schemas.CreateOnePoem_Req, db: AsyncSession):
    try:
        new_poem = PoemModel(**poem.model_dump())
        db.add(new_poem)
        await db.commit()
        await db.refresh(new_poem)

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="already exists")
        elif "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in POST /poems", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_many(data: list[component_schemas.CreateOnePoem_Req], db: AsyncSession):
    try:
        created_items: list[component_schemas.CreateOnePoem_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_poem = PoemModel(**item.model_dump())
                db.add(new_poem)
                await db.commit()
                await db.refresh(new_poem)

                created_items.append(component_schemas.CreateOnePoem_Res.model_validate(new_poem, from_attributes=True))
            except Exception as e:
                await db.rollback()
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "poem does already exists"
                elif "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
                    msg = "foreign key error"
                else:
                    msg = "Unknown error, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType(
                    item_index=index,
                    message=msg
                    ))

        return component_schemas.CreateManyPoem_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /poems/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_one(id: UUID, data: component_schemas.UpdatePoem_Req, cache: GlideClient, db: AsyncSession):
    try:
        stmt = select(PoemModel).where(PoemModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_poem = res.unique().one()

        new_poem_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_poem_data.items():
            setattr(existing_poem, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("poem", id)
        _ = await cache.delete([cache_key])
 
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="already exists")
        elif "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in PUST /poems/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_one(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        stmt = delete(PoemModel).where(PoemModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("poem", id)
        _ = await cache.delete([cache_key])

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error when deleting poem", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

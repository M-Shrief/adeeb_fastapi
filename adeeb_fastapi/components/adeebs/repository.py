from fastapi import status
from glide import GlideClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.models import Adeeb as AdeebModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import adeebs as adeeb_schemas, api as api_schemas
from adeeb_fastapi.components.adeebs import schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(AdeebModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        # We can get the data by: data = [row[0] for row in rows], 
        # but we merge fetching the data & validation in the same step.
        adeebs =  [adeeb_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema](data=adeebs, total_count=total_count, limit=queries.limit, offset=queries.offset)  
    except Exception as e:
        logger.error(error=e, msg="Error in GET /adeebs")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def get_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        cache_key = format_key_by_id("adeeb", id)
        cache_res = await cache_get(cache_key, cache)

        if cache_res is not None:
            adeeb = component_schemas.GetAdeeb_Res.model_validate(cache_res, from_attributes=True)
        else:
            stmt = select(AdeebModel).where(AdeebModel.id == id)
            stmt = stmt.options(joins.poems_to_adeeb).options(joins.chosen_verses_to_adeeb).options(joins.prose_qoutes_to_adeeb)
            res = await db.scalars(statement=stmt)
            adeeb = res.unique().one()

            adeeb = component_schemas.GetAdeeb_Res.model_validate(adeeb, from_attributes=True)
            
            await cache_set(
                    key=cache_key,
                    value=adeeb,
                    client=cache
                )

        return adeeb
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /adeebs/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_one(adeeb: component_schemas.CreateOneAdeeb_Req, db: AsyncSession):
    try:
        new_adeeb = AdeebModel(**adeeb.model_dump())
        db.add(new_adeeb)
        await db.commit()
        await db.refresh(new_adeeb)

        return new_adeeb

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository")
        else:
            logger.error("Error in POST /adeebs", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_many(data: list[component_schemas.CreateOneAdeeb_Req], db: AsyncSession):
    try:
        created_items: list[component_schemas.CreateOneAdeeb_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_adeeb = AdeebModel(**item.model_dump())
                db.add(new_adeeb)
                await db.commit()
                await db.refresh(new_adeeb)

                created_items.append(component_schemas.CreateOneAdeeb_Res.model_validate(new_adeeb, from_attributes=True))
            except Exception as e:
                await db.rollback()
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "adeeb does already exists"
                else:
                    msg = "An error occurred while creating a adeeb, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType(
                    item_index=index,
                    message=msg
                    ))

        return component_schemas.CreateManyAdeeb_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /adeebs/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_one(id: UUID, data: component_schemas.UpdateAdeeb_Req, cache: GlideClient, db: AsyncSession):
    try:
        stmt = select(AdeebModel).where(AdeebModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_adeeb = res.unique().one()

        new_adeeb_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_adeeb_data.items():
            setattr(existing_adeeb, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("adeeb", id)
        _ = await cache.delete([cache_key])
 
        return  

    except Exception as e:
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="already exists")
        else:
            logger.error("Error in PUST /adeebs/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_one(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        stmt = delete(AdeebModel).where(AdeebModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        # Delete from cache after deletion to prevent showing deleted data
        cache_key = format_key_by_id("adeeb", id)
        _ = await cache.delete([cache_key])

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error when deleting adeeb", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

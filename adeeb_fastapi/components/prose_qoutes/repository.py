from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.models import ProseQoute as ProseQouteModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.schemas import prose_qoutes as prose_qoutes_schemas, api as api_schemas
from adeeb_fastapi.components.prose_qoutes import schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(ProseQouteModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0 
        prose_qoutes =  [prose_qoutes_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[prose_qoutes_schemas.DescriptiveSchema](data=prose_qoutes, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /prose_qoutes")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def get_one_by_id(id: UUID, db: AsyncSession):
    try:
        stmt = select(ProseQouteModel).where(ProseQouteModel.id == id)
        stmt = stmt.options(joins.adeebs_to_prose_qoutes)
        res = await db.scalars(statement=stmt)
        prose_qoute = res.unique().one()
        return prose_qoute
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /prose_qoutes/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_one(prose_qoute: component_schemas.CreateOneProseQoute_Req, db: AsyncSession):
    try:
        new_prose_qoute = ProseQouteModel(**prose_qoute.model_dump())
        db.add(new_prose_qoute)
        await db.commit()
        await db.refresh(new_prose_qoute)

        return new_prose_qoute

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in POST /prose_qoutes", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def create_many(data: list[component_schemas.CreateOneProseQoute_Req], db: AsyncSession):
    try:
        created_items: list[component_schemas.CreateOneProseQoute_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType] = []

        for index, item in enumerate(data):
            try:
                new_prose_qoute = ProseQouteModel(**item.model_dump())
                db.add(new_prose_qoute)
                await db.commit()
                await db.refresh(new_prose_qoute)

                created_items.append(component_schemas.CreateOneProseQoute_Res.model_validate(new_prose_qoute, from_attributes=True))
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

        return component_schemas.CreateManyProseQoute_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )

    except Exception as e:
        logger.error("Error in POST /prose_qoutes/many", error=e)
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_one(id: UUID, data: component_schemas.UpdateProseQoute_Req, db: AsyncSession):
    try:
        stmt = select(ProseQouteModel).where(ProseQouteModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_prose_qoute = res.unique().one()

        new_prose_qoute_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_prose_qoute_data.items():
            setattr(existing_prose_qoute, key, value)

        await db.commit()
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in PUT /prose_qoutes/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_one(id: UUID, db: AsyncSession):
    try:
        stmt = delete(ProseQouteModel).where(ProseQouteModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in DELETE /prose_qoutes/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

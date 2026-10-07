

from uuid import UUID

from fastapi import status
from glide import GlideClient
from sqlalchemy.ext.asyncio import AsyncSession
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.components.adeebs import repository, schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        repo_result = await repository.get_all(queries, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /adeebs")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        result = await repository.get_one_by_id(id, cache, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /adeebs/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_one(adeeb: component_schemas.CreateOneAdeeb_Req, db: AsyncSession):
    try:
        result = await repository.create_one(adeeb, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /adeebs", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_many(data: list[component_schemas.CreateOneAdeeb_Req], db: AsyncSession):
    try: 
        result = await repository.create_many(data, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /adeebs/many", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")
        

async def update_one(id: UUID, data: component_schemas.UpdateAdeeb_Req, cache: GlideClient, db: AsyncSession):
    try: 
        result = await repository.update_one(id, data, cache, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /adeebs/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_one(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        await repository.delete_one(id, cache, db)
        return
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in DELETE /adeebs/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")

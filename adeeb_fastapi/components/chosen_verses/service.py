from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.schemas import api as api_schemas
from adeeb_fastapi.components.chosen_verses import repository, schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        repo_result = await repository.get_all(queries, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /chosen_verses")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_one_by_id(id: UUID, db: AsyncSession):
    try:
        result = await repository.get_one_by_id(id, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /chosen_verses/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_one(chosen_verse: component_schemas.CreateOneChosenVerses_Req, db: AsyncSession):
    try:
        result = await repository.create_one(chosen_verse, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /chosen_verses", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def create_many(data: list[component_schemas.CreateOneChosenVerses_Req], db: AsyncSession):
    try: 
        result = await repository.create_many(data, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /chosen_verses/many", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")
        

async def update_one(id: UUID, data: component_schemas.UpdateChosenVerses_Req, db: AsyncSession):
    try: 
        result = await repository.update_one(id, data, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /chosen_verses/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_one(id: UUID, db: AsyncSession):
    try:
        await repository.delete_one(id, db)
        return
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in DELETE /chosen_verses/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")

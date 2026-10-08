from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID
from glide import GlideClient
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.cache.index import get_async_cache
from adeeb_fastapi.schemas import adeebs as adeeb_schemas, api as api_schemas
from adeeb_fastapi.components.adeebs import schemas as component_schemas, service

router = APIRouter(tags=["Adeebs"])

@router.get(
    "/adeebs",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_adeebs(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        response_result = await service.get_all(queries, db)
        return response_result
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /adeebs", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/adeebs/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetAdeeb_Res,
    response_model_exclude_none=True
)
async def get_adeeb_by_id(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        adeeb = await service.get_one_by_id(id, cache, db)
        return adeeb
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="adeeb is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /adeebs/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/adeebs",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneAdeeb_Res,
    response_model_exclude_none=True
)
async def create_adeeb(adeeb: component_schemas.CreateOneAdeeb_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_adeeb = await service.create_one(adeeb, db)
        return new_adeeb
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="adeeb does already exists")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /adeebs", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/adeebs/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyAdeeb_Res,
    response_model_exclude_none=True
)
async def create_adeebs(data: list[component_schemas.CreateOneAdeeb_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result = await service.create_many(data, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /adeebs/many", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/adeebs/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_adeeb(id: UUID, data: component_schemas.UpdateAdeeb_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.update_one(id, data, cache, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="adeeb already exists")
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="adeeb is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /adeebs/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/adeebs/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_adeeb(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.delete_one(id, cache, db)
        return
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="adeeb is referenced in other places")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /adeebs/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
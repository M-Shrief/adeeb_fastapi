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
from adeeb_fastapi.schemas import poems as poems_schemas, api as api_schemas
from adeeb_fastapi.components.poems import schemas as component_schemas, service


router = APIRouter(tags=["Poems"])

@router.get(
    "/poems",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_poems(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        response_result = await service.get_all(queries, db)
        return response_result
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /poems", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/poems/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetPoem_Res,
    response_model_exclude_none=True
)
async def get_poem_by_id(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        poem = await service.get_one_by_id(id, cache, db)
        return poem
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poem is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /poems/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/poems",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOnePoem_Res,
    response_model_exclude_none=True
)
async def create_poem(poem: component_schemas.CreateOnePoem_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_poem = await service.create_one(poem, db)
        return new_poem
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /poems", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unknown error, try agian later")

@router.post(
    path="/poems/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyPoem_Res,
    response_model_exclude_none=True
)
async def create_poems(data: list[component_schemas.CreateOnePoem_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result: component_schemas.CreateManyPoem_Res = await service.create_many(data, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /poems/many", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/poems/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_poem(id: UUID, data: component_schemas.UpdatePoem_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.update_one(id, data, cache, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poem is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /poems/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/poems/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_poem(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.delete_one(id, cache, db)
        return
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="poem is referenced in other places")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /poems/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
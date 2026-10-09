from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.schemas import prose_qoutes as prose_qoutes_schemas, api as api_schemas
from adeeb_fastapi.components.prose_qoutes import schemas as component_schemas, service



router = APIRouter(tags=["ProseQoutes"])

@router.get(
    "/prose_qoutes",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[prose_qoutes_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_prose_qoutes(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        response_result = await service.get_all(queries, db)
        return response_result
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /prose_qoutes", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/prose_qoutes/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetProseQoute_Res,
    response_model_exclude_none=True
)
async def get_prose_qoute_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        prose_qoute = await service.get_one_by_id(id, db)
        return prose_qoute

    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prose_qoute is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /prose_qoutes/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/prose_qoutes",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneProseQoute_Res,
    response_model_exclude_none=True
)
async def create_prose_qoute(data: component_schemas.CreateOneProseQoute_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_prose_qoute= await service.create_one(data, db)
        return new_prose_qoute
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /prose_qoute", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    path="/prose_qoutes/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyProseQoute_Res,
    response_model_exclude_none=True
)
async def create_prose_qoutes(data: list[component_schemas.CreateOneProseQoute_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result = await service.create_many(data, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /prose_qoutes/many", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/prose_qoutes/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_prose_qoute(id: UUID, data: component_schemas.UpdateProseQoute_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.update_one(id, data, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prose_qoute is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /prose_qoutes/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/prose_qoutes/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_prose_qoute(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.delete_one(id, db)
        return
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="prose_qoute is referenced in other places")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /prose_qoutes/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

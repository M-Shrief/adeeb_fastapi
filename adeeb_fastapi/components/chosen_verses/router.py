from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID
# ###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.schemas import chosen_verses as chosen_verses_schemas, api as api_schemas
from adeeb_fastapi.components.chosen_verses import schemas as component_schemas, service


router = APIRouter(tags=["ChosenVersess"])

@router.get(
    "/chosen_verses",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[chosen_verses_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_chosen_verses(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        response_result = await service.get_all(queries, db)
        return response_result
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /chosen_verses", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/chosen_verses/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetChosenVerses_Res,
    response_model_exclude_none=True
)
async def get_chosen_verses_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        chosen_verse = await service.get_one_by_id(id, db)
        return chosen_verse

    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chosen_verse is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in GET /chosen_verses/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/chosen_verses",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneChosenVerses_Res,
    response_model_exclude_none=True
)
async def create_one_chosen_verses(data: component_schemas.CreateOneChosenVerses_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_chosen_verse= await service.create_one(data, db)
        return new_chosen_verse
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /chosen_verses", error=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown error, try agian later")

@router.post(
    path="/chosen_verses/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyChosenVerses_Res,
    response_model_exclude_none=True
)
async def create_many_chosen_verses(data: list[component_schemas.CreateOneChosenVerses_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        result = await service.create_many(data, db)
        return result 
    except APIError as e:
        match e.status_code:
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in POST /chosen_verses/many", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.put(
    "/chosen_verses/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_chosen_verses(id: UUID, data: component_schemas.UpdateChosenVerses_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.update_one(id, data, db)
        return 
    except APIError as e:
        match e.status_code:
            case status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chosen_verse is not found")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in PUT /chosen_verses/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/chosen_verses/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chosen_verses(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        await service.delete_one(id, db)
        return
    except APIError as e:
        match e.status_code:
            case status.HTTP_409_CONFLICT:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="chosen_verse is referenced in other places")
            case status.HTTP_400_BAD_REQUEST:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")
    except Exception as e:
        logger.error("Error in DELETE /chosen_verses/{id}", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

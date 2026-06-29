from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Literal
from uuid import UUID
from glide import GlideClient
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Poem as PoemModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.cache.index import get_async_cache, cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import poems as poems_schemas, api as api_schemas
from adeeb_fastapi.components.poems import schemas as component_schemas



router = APIRouter(tags=["Poems"])

@router.get(
    "/poems",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_poems(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(PoemModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0 
        poems =  [poems_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[poems_schemas.DescriptiveSchema](data=poems, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting poems", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/poems/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetPoem_Res,
    response_model_exclude_none=True
)
async def get_poem_by_id(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="poem is not found!")
    except Exception as e:
        logger.error("Error when getting a poem by id", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/poems",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOnePoem_Res,
    response_model_exclude_none=True
)
async def create_poem(poem: component_schemas.CreateOnePoem_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_poem = PoemModel(**poem.model_dump())
        db.add(new_poem)
        await db.commit()
        await db.refresh(new_poem)

        return new_poem

    except Exception as e:
        logger.error("Error occurred while creating a poem", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "poem does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a poem, try again later."
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail_msg)

@router.post(
    path="/poems/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyPoem_Res,
    response_model_exclude_none=True
)
async def create_poems(data: list[component_schemas.CreateOnePoem_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        created_items: list[component_schemas.CreateOnePoem_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType[component_schemas.CreateOnePoem_Req]] = []

        for item in data:
            try:
                new_poem = PoemModel(**item.model_dump())
                db.add(new_poem)
                await db.commit()
                await db.refresh(new_poem)

                created_items.append(component_schemas.CreateOnePoem_Res.model_validate(new_poem, from_attributes=True))
            except Exception as e:
                logger.error("Error occurred while creating a poem", error=e)
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "poem does already exists"
                else:
                    msg = "An error occurred while creating a poem, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType[component_schemas.CreateOnePoem_Req](
                    item=item,
                    message=msg
                    ))

        return component_schemas.CreateManyPoem_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )


    except Exception as e:
        detail_msg = "An error occurred while creating many poem entities, try again later."
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail_msg)

@router.put(
    "/poems/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_poem(id: UUID, req_body: component_schemas.UpdatePoem_Req, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(PoemModel).where(PoemModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_poem = res.unique().one()

        new_poem_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_poem_data.items():
            setattr(existing_poem, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("poem", id)
        _ = await cache.delete([cache_key])
 
        return api_schemas.Update_Res()
        
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poem is not found!")
    except Exception as e:
        logger.error("Error when updating poem", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/poems/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_poem(id: UUID, cache: Annotated[GlideClient, Depends(get_async_cache)], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = delete(PoemModel).where(PoemModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

       # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("poem", id)
        _ = await cache.delete([cache_key])
 
        return api_schemas.Delete_Res()
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poem is not found!")
    except Exception as e:
        logger.error("Error when deleting poem", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

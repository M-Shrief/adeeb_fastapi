from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from sqlalchemy.orm import joinedload, load_only
from typing import Annotated, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import Adeeb as AdeebModel
from adeeb_fastapi.database import joins
from adeeb_fastapi.schemas import adeebs as adeeb_schemas, api as api_schemas
from adeeb_fastapi.components.adeebs import schemas as component_schemas


router = APIRouter(tags=["Adeebs"])

@router.get(
    "/adeebs",
    status_code=status.HTTP_200_OK,
    response_model=api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema],
    response_model_exclude_none=True,
)
async def get_adeebs(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try: #
        stmt = select(AdeebModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[1].total if rows else 0 # note: using 0 or 1 is the same, as count().over()...etc returns total_count with every row
        # We can get the data by: data = [row[0] for row in rows], 
        # but we merge fetching the data & validation in the same step.
        adeebs =  [adeeb_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[adeeb_schemas.DescriptiveSchema](data=adeebs, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except Exception as e:
        logger.error("Error when getting adeebs", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/adeebs/{id}",
    status_code=status.HTTP_200_OK,
    response_model=component_schemas.GetAdeeb_Res,
    response_model_exclude_none=True
)
async def get_adeeb_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(AdeebModel).where(AdeebModel.id == id)
        stmt = stmt.options(joins.poems_to_adeeb).options(joins.chosen_verses_to_adeeb).options(joins.prose_qoutes_to_adeeb)
        res = await db.scalars(statement=stmt)
        adeeb = res.unique().one()
        return adeeb

    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="adeeb is not found!")
    except Exception as e:
        logger.error("Error when getting a adeeb by id", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.post(
    path="/adeebs",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateOneAdeeb_Res,
    response_model_exclude_none=True
)
async def create_adeeb(adeeb: component_schemas.CreateOneAdeeb_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        new_adeeb = AdeebModel(**adeeb.model_dump())
        db.add(new_adeeb)
        await db.commit()
        await db.refresh(new_adeeb)

        return new_adeeb

    except Exception as e:
        logger.error("Error occurred while creating a adeeb", error=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "adeeb does already exists"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while creating a adeeb, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.post(
    path="/adeebs/many",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.CreateManyAdeeb_Res,
    response_model_exclude_none=True
)
async def create_adeebs(data: list[component_schemas.CreateOneAdeeb_Req], db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        created_items: list[component_schemas.CreateOneAdeeb_Res] = []
        invalid_items: list[api_schemas.InvalidDataFieldType[component_schemas.CreateOneAdeeb_Req]] = []

        for item in data:
            try:
                new_adeeb = AdeebModel(**item.model_dump())
                db.add(new_adeeb)
                await db.commit()
                await db.refresh(new_adeeb)

                created_items.append(component_schemas.CreateOneAdeeb_Res.model_validate(new_adeeb, from_attributes=True))
            except Exception as e:
                logger.error("Error occurred while creating a adeeb", error=e)
                if "psycopg.errors.UniqueViolation" in str(e):
                    msg = "adeeb does already exists"
                else:
                    msg = "An error occurred while creating a adeeb, try again later."                

                invalid_items.append(api_schemas.InvalidDataFieldType[component_schemas.CreateOneAdeeb_Req](
                    item=item,
                    message=msg
                    ))

        return component_schemas.CreateManyAdeeb_Res(
            created_items=created_items,
            success_count=len(created_items),
            invalid_items=invalid_items
        )


    except Exception as e:
        detail_msg = "An error occurred while creating many adeeb entities, try again later."
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.put(
    "/adeebs/{id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Update_Res,
    response_model_exclude_none=True
)
async def update_adeeb(id: UUID, req_body: component_schemas.UpdateAdeeb_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(AdeebModel).where(AdeebModel.id == id)
        res = await db.scalars(statement=stmt)    
        existing_adeeb = res.unique().one()

        new_adeeb_data = req_body.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_adeeb_data.items():
            setattr(existing_adeeb, key, value)

        await db.commit()
        return api_schemas.Update_Res()
        
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adeeb is not found!")
    except Exception as e:
        logger.error("Error when updating adeeb", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.delete(
    "/adeebs/{id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=api_schemas.Delete_Res,
    response_model_exclude_none=True
)
async def delete_adeeb(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = delete(AdeebModel).where(AdeebModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        return api_schemas.Delete_Res()
    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adeeb is not found!")
    except Exception as e:
        logger.error("Error when deleting adeeb", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

from typing import Literal
from fastapi import status
from glide import FlushMode, GlideClient, TEncodable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func, update
from uuid import UUID, uuid4
###
from adeeb_fastapi.components.users.jwt import schemas as component_schemas
from adeeb_fastapi.database import joins
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import time as time_utils
from adeeb_fastapi.auth import jwts
from adeeb_fastapi.database.models import JWT as JWTModel
from adeeb_fastapi.cache.index import cache_get, cache_set, format_key_by_id
from adeeb_fastapi.schemas import api as api_schemas, jwt as jwt_schemas

async def new_tokens(user: jwt_schemas.Claims_User, cache: GlideClient, db: AsyncSession, family_id: UUID | None = None):
    """return JWT claims for access & refresh token respectively"""
    try:
        if family_id is None:
            # shared family_id
            family_id= uuid4()

        access_model = JWTModel(
            user_id=user.id,
            family_id=family_id,
            is_banned=False,
            token_type=jwt_schemas.TokenTypeEnum.ACCESS,
            exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
            iat=time_utils.Now(),
        )

        refresh_model = JWTModel(
            user_id=user.id,
            family_id=family_id,
            used=False,
            is_banned=False,
            token_type=jwt_schemas.TokenTypeEnum.REFRESH,
            exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN), # 7 days
            iat=time_utils.Now(),
        )
        # even if access model is short-lived we save it,
        # so we can ban tokens by their family_id and remove them from caching afterward
        db.add_all([access_model, refresh_model]) 
        await db.commit()
        await db.refresh(access_model)
        await db.refresh(refresh_model)


        access_schema = jwt_schemas.FullSchema(
            jti=access_model.jti,
            family_id=access_model.family_id,
            user_id=access_model.user_id,
            token_type=access_model.token_type,
            is_banned=access_model.is_banned,
            used=access_model.used,
            exp=access_model.exp,
            iat=access_model.iat,
        )

        # After we create to the token, we also added to cache,
        # as it's most likely the user will continue using the service
        await cache_set(
            key=format_key_by_id("jwts", access_schema.jti),
            value=access_schema,
            client=cache,
            exp=60 * 15 # 15 m
        )

        access_claims = jwts.new_claims(user, model=access_model)
        refresh_claims = jwts.new_claims(user, model=refresh_model, token_type="refresh")

        if access_claims is None or refresh_claims is None:
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

        access_token = jwts.create_jwt(access_claims)
        refresh_token = jwts.create_jwt(refresh_claims)

        return access_token, refresh_token
    except Exception as e:
        await db.rollback()
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error("Error in creating new claims", error=e, caused_in="repository")
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession, family_id: UUID | None = None, user_id: UUID | None = None):
    try:
        stmt = select(JWTModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)
        if family_id is not None:
            stmt = stmt.where(JWTModel.family_id == family_id)
        if user_id is not None:
            stmt = stmt.where(JWTModel.user_id == user_id)
            
        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0
        # We can get the data by: data = [row[0] for row in rows], 
        # but we merge fetching the data & validation in the same step.
        jwts =  [jwt_schemas.FullSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[jwt_schemas.FullSchema](data=jwts, total_count=total_count, limit=queries.limit, offset=queries.offset)  
    except Exception as e:
        logger.error(error=e, msg="Error in GET /jwts")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def get_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        cache_key = format_key_by_id("jwts", id)
        cache_res = await cache_get(cache_key, cache)
        if cache_res is not None:
            jwt = component_schemas.GetOne_Res_Body.model_validate(cache_res, from_attributes=True)
            logger.info("cache")
        else: # we don't set new tokes o
            stmt = select(JWTModel).where(JWTModel.jti == id)
            stmt = stmt.options(joins.user_to_jwt)
            res = await db.scalars(statement=stmt)
            jwt = res.unique().one()
            jwt = component_schemas.GetOne_Res_Body.model_validate(jwt, from_attributes=True)
            logger.info("db")

        return jwt
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error(f"Error in getting jwt:{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def is_banned(id: UUID, cache: GlideClient, db: AsyncSession)-> bool:
    """Used Internally only"""
    try:
        jwt_token = await get_one_by_id(id, cache, db)
        return jwt_token.is_banned
        
    except APIError:
        return False

async def update_one(id: UUID, data: component_schemas.UpdateOne_Req_Body, cache: GlideClient, db: AsyncSession):
    try:
        stmt = select(JWTModel).where(JWTModel.jti == id)
        res = await db.scalars(statement=stmt)    
        existing_jwt = res.unique().one()

        new_jwt_data = data.model_dump(exclude_none=True)  # Exclude None fields from the request body

        for key, value in new_jwt_data.items():
            setattr(existing_jwt, key, value)

        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("jwts", id)
        _ = await cache.delete([cache_key])
 
        return  

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e): # (SQLSTATE 23503)
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="foreign key error")
        else:
            logger.error(f"Error in updating jwt:{id}", error=e, caused_in="repository")
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def ban_one_by_id(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        data = component_schemas.UpdateOne_Req_Body.model_validate({"is_banned":True})
        _ = await update_one(id, data, cache, db)
        return        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in banning token, id:{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def ban_jwts_with_filters(cache: GlideClient, db: AsyncSession, family_id: UUID | None = None, user_id: UUID | None = None):
    try:
        stmt = select(JWTModel)
        if family_id is not None:
            stmt = stmt.where(JWTModel.family_id == family_id)
        if user_id is not None:
            stmt = stmt.where(JWTModel.user_id == user_id)

        resp  = await db.execute(stmt)
        rows = resp.scalars()

        cache_keys: list[TEncodable] = [] 
        # First delete user's token in cache
        for token in rows:
            cache_key = format_key_by_id("jwts", token.jti)
            cache_keys.append(cache_key)

        # if there's no token for the user, then raise 404 APIError
        if len(cache_keys) == 0:
            raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")

        # Delete all tokens from cache
        _ = await cache.delete(cache_keys)

        # then update all records using family_id
        stmt = update(JWTModel).values(is_banned=True)
        if family_id is not None:
            stmt = stmt.where(JWTModel.family_id == family_id)
        if user_id is not None:
            stmt = stmt.where(JWTModel.user_id == user_id)

        _ = await db.execute(stmt)
        _ = await db.commit()
        return

    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in banning family tokens, family_id:{family_id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_user_jwts(user_id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        stmt = select(JWTModel).where(JWTModel.user_id == user_id)
        resp  = await db.execute(stmt)
        rows = resp.scalars()

        cache_keys: list[TEncodable] = [] 
        # First delete user's token in cache
        for token in rows:
            cache_key = format_key_by_id("jwts", token.jti)
            cache_keys.append(cache_key)

        # if there's no token for the user, then raise 404 APIError
        if len(cache_keys) == 0:
            raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")

        # Delete all tokens from cache
        _ = await cache.delete(cache_keys)


        # Delete user's jwt tokens
        stmt = delete(JWTModel).where(JWTModel.user_id == user_id)
        _ = await db.execute(statement=stmt)
        await db.commit()

    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in banning user tokens, user_id:{user_id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def delete_one(id: UUID, cache: GlideClient, db: AsyncSession):
    try:
        stmt = delete(JWTModel).where(JWTModel.jti == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        # Delete from cache after update to prevent showing old data
        cache_key = format_key_by_id("jwts", id)
        _ = await cache.delete([cache_key])

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error(f"Error in deleting jwt:{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def cleanup(cache: GlideClient, db: AsyncSession):
    try:
        stmt = delete(JWTModel).where(JWTModel.exp < time_utils.Now().date())
        _ = await db.execute(statement=stmt)
        await db.commit()

        _ = await cache.flushall(flush_mode=FlushMode.ASYNC)
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in jwts cleanup()", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

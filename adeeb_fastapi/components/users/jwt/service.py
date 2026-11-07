from fastapi import status
from glide import  GlideClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.auth import jwts, errors as auth_errors, utils as auth_utils
from adeeb_fastapi.schemas import api as api_schemas, jwt as jwt_schemas
from adeeb_fastapi.components.users.jwt import repository, schemas as component_schemas


async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, token: str, db: AsyncSession, family_id: UUID | None = None, user_id: UUID | None = None):
    try:
        _ = await auth_utils.verifying_admin_user(token, "read", "service")

        repo_result = await repository.get_all(queries, db, family_id=family_id, user_id=user_id)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /jwts")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def get_one_by_id(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "read", "service")

        result = await repository.get_one_by_id(id, cache, db)
        return result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /jwts/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def refresh(token: str, cache: GlideClient, db: AsyncSession):
    try:
        claims, error = jwts.verify_jwt(token, jwt_schemas.TokenTypeEnum.REFRESH)
        if error is not None or claims is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_TOKEN, caused_in="service")

        token_data = await repository.get_one_by_id(claims.jti, cache, db)
        if token_data.is_banned:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.BANNED, caused_in="service")
        elif token_data.used is True:
            _ = await repository.ban_jwts_with_filters(cache, db, family_id=token_data.family_id)
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.USED, caused_in="service")
        else:
            # After checking that the refresh token and it's family isn't banned,
            # We need to be careful if user's roles & permissions was changed, like if he was banned.
            # That's why we join the user data when querying the token. 
            claims_user = jwt_schemas.Claims_User(id=token_data.user.id, username=token_data.user.username, roles=token_data.user.roles)
            access_token, refresh_token = await repository.new_tokens(claims_user, cache, db, token_data.family_id)

            # After creating new tokens, we should flag the refresh token as used, better be a background task.
            # We don't need to handle 404 error, as we already know it exists if it's a valid token
            await repository.update_one(token_data.jti, component_schemas.UpdateOne_Req_Body.model_validate({"used": True}), cache, db)

            return access_token, refresh_token
    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error("Error in GET /jwts/refresh", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_one(id: UUID, token: str, data: component_schemas.UpdateOne_Req_Body, cache: GlideClient, db: AsyncSession):
    try: 
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        result = await repository.update_one(id, data, cache, db)
        return result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /jwts/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def ban_one_by_id(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try: 
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await repository.ban_one_by_id(id, cache, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /jwts/{id}/ban", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def ban_jwts_with_filters(token: str, cache: GlideClient, db: AsyncSession, family_id: UUID | None = None, user_id: UUID | None = None):
    try: 
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await repository.ban_jwts_with_filters(cache, db, family_id, user_id)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /jwts/family/{family_id}/ban", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_one(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await repository.delete_one(id, cache, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in DELETE /jwts/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")


async def cleanup(token: str, cache: GlideClient, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await repository.cleanup(cache, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in DELETE /jwts/cleanup", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")


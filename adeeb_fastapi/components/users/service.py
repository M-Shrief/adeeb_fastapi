from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from glide import GlideClient
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.auth import errors as auth_errors, utils as auth_utils, passwords
from adeeb_fastapi.schemas import api as api_schemas, users as users_schemas, jwt as  jwt_schemas
from adeeb_fastapi.components.users import repository, schemas as component_schemas
from adeeb_fastapi.components.users.jwt import repository as jwt_repository



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, token: str, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "read", "service")
        repo_result = await repository.get_all(queries, db)
        return repo_result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /users")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def get_current_user(token: str, db: AsyncSession):
    try:
        claims = await auth_utils.verifying_normal_user(token, "read", "service")

        if claims.user is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_CLAIMS, caused_in="service")

        result = await repository.get_one_by_id(claims.user.id, db)
        return result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def get_one_by_id(id: UUID, token: str, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "read", "service")
        result = await repository.get_one_by_id(id, db)
        return result

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def signup(data: component_schemas.UserSignup_Req, cache: GlideClient, db: AsyncSession):
    try:
        user = await repository.signup(data, db)
        claims_user = jwt_schemas.Claims_User(id=user.id, username=user.username, roles=user.roles)
        access_token, refresh_token = await jwt_repository.new_tokens(claims_user, cache, db)
        return component_schemas.UserAuth_Res(user=user, access_token=access_token), refresh_token
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /users/signup", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def login(data: component_schemas.UserLogin_Req, cache: GlideClient, db: AsyncSession):
    try:
        user = await repository.get_one_for_login(data.username, db)
        is_password_verified = await passwords.verify_password(data.password, user.password)
        if is_password_verified is False: # if password is incorrect.
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_PASS, caused_in="service")
        
        claims_user = jwt_schemas.Claims_User(id=user.id, username=user.username, roles=user.roles)
        access_token, refresh_token = await jwt_repository.new_tokens(claims_user, cache, db)
        return component_schemas.UserAuth_Res(
            user=users_schemas.DescriptiveSchema(id=user.id, username=user.username, roles=user.roles), 
            access_token=access_token,
        ), refresh_token

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /users/login", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")
        
async def update_current_user(token: str, data: component_schemas.UpdateCurrentUser_Req, db: AsyncSession):
    try: 
        claims = await auth_utils.verifying_normal_user(token, "write", "service")
        if claims.user is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_CLAIMS, caused_in="service")

        await repository.update_current_user(claims.user.id, data, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /users/me", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_user_by_id(id: UUID, token: str, data: component_schemas.UpdateUserById_Req, db: AsyncSession):
    try: 
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await repository.update_user_by_id(id, data, db)
        return 

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in PUT /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def ban_user_by_id(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try: 
        _ = await auth_utils.verifying_admin_user(token, "write", "service")

        await jwt_repository.ban_jwts_with_filters(cache, db, user_id=id, family_id=None)

        await repository.ban_user_by_id(id, db)

        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in PUT /users/{id}/ban", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_current_user(token: str, cache: GlideClient, db: AsyncSession):
    try:
        claims = await auth_utils.verifying_normal_user(token, "write", "service")
        if claims.user is None:
            raise auth_errors.AuthError(reason=auth_errors.AuthError_ReasonEnum.INVALID_CLAIMS, caused_in="service")

        await jwt_repository.delete_user_jwts(claims.user.id, cache, db)
        await repository.delete_one(claims.user.id, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")

async def delete_one(id: UUID, token: str, cache: GlideClient, db: AsyncSession):
    try:
        _ = await auth_utils.verifying_admin_user(token, "write", "service")
        await jwt_repository.delete_user_jwts(id, cache, db)
        await repository.delete_one(id, db)
        return

    except auth_errors.AuthError as e:
        raise e
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")

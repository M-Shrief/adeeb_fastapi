from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from glide import GlideClient
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.auth import jwts, errors as auth_errors, utils as auth_utils, passwords
from adeeb_fastapi.schemas import api as api_schemas, users as users_schemas, jwt as  jwt_schemas
from adeeb_fastapi.components.users import repository, schemas as component_schemas
from adeeb_fastapi.components.users.jwt import repository as jwt_repository


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
        if passwords.verify_password(data.password, user.password) is False: # if password is incorrect.
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

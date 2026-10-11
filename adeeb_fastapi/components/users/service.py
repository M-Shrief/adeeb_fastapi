from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.schemas import api as api_schemas, users as users_schemas
from adeeb_fastapi.components.users import repository, schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, Authorization: str, db: AsyncSession):
    try:

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "read")
        if is_administrator is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        repo_result = await repository.get_all(queries, db)
        return repo_result
    except APIError as e:
        raise e 
    except Exception as e:
        logger.error(error=e, msg="Error in GET /users")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_current_user(Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Normal, "read"),
        ]

        is_permitted = auth_utils.check_permission(authorized_list, permissions, "read")
        if is_permitted is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        user = payload["user"]
        id = user["id"]
        result = await repository.get_one_by_id(id, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def get_one_by_id(id: UUID, Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or  payload is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "read")
        if is_administrator is False:
            raise APIError(status_code=status.HTTP_401_UNAUTHORIZED, caused_in="service")

        result = await repository.get_one_by_id(id, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def signup(data: component_schemas.UserSignup_Req, db: AsyncSession):
    try:
        user = await repository.signup(data, db)
        access_token = auth_utils.create_jwt(id=user.id, username=user.username, roles=user.roles)
        return component_schemas.UserAuth_Res(user=user, access_token=access_token)
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /users/signup", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def login(data: component_schemas.UserLogin_Req, db: AsyncSession):
    try:
        user = await repository.get_one_for_login(data.username, db)
        if auth_utils.verify_password(data.password, user.password) is False: # if password is incorrect.
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")
        access_token = auth_utils.create_jwt(id=user.id, username=user.username, roles=user.roles)
        return component_schemas.UserAuth_Res(
            user=users_schemas.DescriptiveSchema(id=user.id, username=user.username, roles=user.roles), 
            access_token=access_token,
        )

    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in POST /users/login", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")
        

async def update_current_user(Authorization: str, data: component_schemas.UpdateCurrentUser_Req, db: AsyncSession):
    try: 
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or payload is None :
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Normal, "write"),
        ]

        is_permitted = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_permitted is False:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        user = payload["user"]
        id= user["id"]
        result = await repository.update_current_user(id, data, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error("Error in PUT /users/me", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def update_user_by_id(id: UUID, Authorization: str, data: component_schemas.UpdateUserById_Req, db: AsyncSession):
    try: 
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or payload is None :
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        result = await repository.update_user_by_id(id, data, db)
        return result
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in PUT /users/{id}", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")

async def ban_user_by_id(id: UUID, Authorization: str, db: AsyncSession):
    try: 
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or payload is None :
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        await repository.ban_user_by_id(id, db)
        return
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in PUT /users/{id}/ban", error=e, caused_in="service")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="service")


async def delete_current_user(Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or payload is None :
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Normal, "write"),
        ]

        is_permitted = auth_utils.check_permission(authorized_list, permissions, "write")
        if is_permitted is False:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        user = payload["user"]
        id= user["id"]
        await repository.delete_one(id, db)
        return
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")


async def delete_one(id: UUID, Authorization: str, db: AsyncSession):
    try:
        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization)
        if verified is False or payload is None :
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        permissions: list[str] | None = payload.get("permissions")
        if permissions is None:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        is_administrator = auth_utils.check_adminstration(permissions, "write")
        if is_administrator is False:
            raise APIError(status.HTTP_401_UNAUTHORIZED, caused_in="service")

        await repository.delete_one(id, db)
        return
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="service")

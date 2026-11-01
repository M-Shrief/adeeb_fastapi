from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Literal
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified
###
from adeeb_fastapi.utils.errors import APIError
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.models import User as UserModel, roles_enum
from adeeb_fastapi.schemas import users as users_schemas, api as api_schemas
from adeeb_fastapi.components.users import schemas as component_schemas



async def get_all(queries: api_schemas.SharedQueriesForGetManyRequests, db: AsyncSession):
    try:
        stmt = select(UserModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0 
        users =  [users_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[users_schemas.DescriptiveSchema](data=users, total_count=total_count, limit=queries.limit, offset=queries.offset)
    except Exception as e:
        logger.error(error=e, msg="Error in GET /users")
        raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def get_one_by_id(id: UUID, db: AsyncSession):
    try:
        stmt = select(UserModel).where(UserModel.id == id)
        resp  = await db.scalars(stmt)
        existing_user = resp.unique().one()
        return existing_user
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in GET /users/{id}", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def signup(user: component_schemas.UserSignup_Req, db: AsyncSession):
    try:
        new_user = UserModel(**user.model_dump())
        new_user.password = auth_utils.hash_password(new_user.password)

        try: # Clean roles from duplicates, and ensure Normal role exists
            new_user.roles = list(set(new_user.roles))
            _ = new_user.roles.index(users_schemas.RoleEnum.Normal)
        except ValueError:
            new_user.roles.append(users_schemas.RoleEnum.Normal)
    
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return users_schemas.DescriptiveSchema(id=new_user.id, username=new_user.username, roles=new_user.roles)

    except Exception as e:
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="Username already exists")
        else:
            logger.error("Error in POST /users", error=e)
            raise APIError(status.HTTP_400_BAD_REQUEST, caused_in="repository")

async def get_one_for_login(username: str, db: AsyncSession):
    try:
        stmt = select(UserModel).where(UserModel.username == username)
        resp  = await db.scalars(stmt)
        existing_user = resp.unique().one()
        return existing_user
    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        logger.error("Error in OIST /users/L", error=e, caused_in="repository")
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_current_user(id: UUID, data: component_schemas.UpdateCurrentUser_Req, db: AsyncSession):
    try:
        stmt = select(UserModel).where(UserModel.id == id) 
        res =  await db.execute(statement=stmt)
        existing_user = res.scalar()

        if existing_user: # User exist in DB

            if data.username is not None:
                existing_user.username = data.username

            if data.password is not None:
                hashed_password = auth_utils.hash_password(data.password)
                existing_user.password = hashed_password

            await db.commit()
            return  
        else:
            # User doesn't exist
            raise APIError(status.HTTP_404_NOT_FOUND, caused_in="repository")

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="Username's already taken")
        else:
            logger.error("Error in PUT /prose_qoutes/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def update_user_by_id(id: UUID, data: component_schemas.UpdateUserById_Req, db: AsyncSession):
    try:
        stmt = select(UserModel).where(UserModel.id == id) 
        res =  await db.execute(statement=stmt)
        existing_user = res.scalar()

        if existing_user: # User exist in DB

            if data.username is not None:
                existing_user.username = data.username

            if data.password is not None:
                hashed_password = auth_utils.hash_password(data.password)
                existing_user.password = hashed_password

            if data.roles is not None:
                try: # Clean roles from duplicates, and ensure Normal role exists
                    roles_set = set(data.roles)
                    roles_set.remove(users_schemas.RoleEnum.Banned) # banning is only accessible in /users/{id}/ban route
                    existing_user.roles = list(roles_set)
                    existing_user.roles
                    _ = existing_user.roles.index(users_schemas.RoleEnum.Normal)
                except ValueError:
                    existing_user.roles.append(users_schemas.RoleEnum.Normal)

            await db.commit()
            return  
        else:
            # User doesn't exist
            raise APIError(status.HTTP_404_NOT_FOUND, caused_in="repository")

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="Username's already taken")
        else:
            logger.error("Error in PUT /prose_qoutes/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def ban_user_by_id(id: UUID, db: AsyncSession):
    try:
        stmt = select(UserModel).where(UserModel.id == id) 
        res =  await db.execute(statement=stmt)
        existing_user = res.scalar()

        if existing_user: # User exist in DB
            try: # Clean roles from duplicates, and check if Banned role already exists
                _ = existing_user.roles.index(users_schemas.RoleEnum.Banned)
            except ValueError:
                existing_user.roles.append(users_schemas.RoleEnum.Banned)
                flag_modified(existing_user, "roles")

            await db.commit()
            return  
        else:
            # User doesn't exist
            raise APIError(status.HTTP_404_NOT_FOUND, caused_in="repository")

    except exc.NoResultFound:
        raise APIError(status_code=status.HTTP_404_NOT_FOUND, caused_in="repository")
    except Exception as e:
        if "psycopg.errors.UniqueViolation" in str(e):
            raise APIError(status.HTTP_409_CONFLICT, caused_in="repository", message="Username's already taken")
        else:
            logger.error("Error in PUT /prose_qoutes/{id}", error=e)
            raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")


async def delete_one(id: UUID, db: AsyncSession):
    try:
        stmt = delete(UserModel).where(UserModel.id == id)
        _ = await db.execute(statement=stmt)
        await db.commit()

        return
    except Exception as e:
        if "psycopg.errors.ForeignKeyViolation" in str(e):
            raise APIError(status_code=status.HTTP_409_CONFLICT, caused_in="repository")        
        logger.error("Error in DELETE /prose_qoutes/{id}", error=e)
        raise APIError(status_code=status.HTTP_400_BAD_REQUEST, caused_in="repository")

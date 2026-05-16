from fastapi import APIRouter, HTTPException, status, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, delete, func
from typing import Annotated, Any, Literal
from uuid import UUID
###
from adeeb_fastapi.utils.logger import logger
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.index import get_async_db
from adeeb_fastapi.database.models import User as UserModel
from adeeb_fastapi.schemas import users as users_schemas, api as api_schemas
from adeeb_fastapi.components.users import schemas as component_schemas


router = APIRouter(tags=["Users"])

@router.get(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=api_schemas.GetAll_Res[component_schemas.GetUser_Res],
    response_model_exclude_none=True    
)
async def get_users(queries: Annotated[api_schemas.SharedQueriesForGetManyRequests, Query()], db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Analytics, "read"),
            auth_utils.create_authorized_item(users_schemas.RoleEnum.DBA, "read"),
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Management, "read"),
        ]

        _, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="read")
        if verified is False:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        stmt = select(UserModel, func.count().over().label('total')).offset(queries.offset).limit(queries.limit)

        resp  = await db.execute(stmt)
        rows = resp.all()

        total_count: int | Literal[0] = rows[0].total if rows else 0 
        users =  [users_schemas.DescriptiveSchema.model_validate(row[0], from_attributes=True) for row in list(rows)]

        return api_schemas.GetAll_Res[users_schemas.DescriptiveSchema](data=users, total_count=total_count, limit=queries.limit, offset=queries.offset)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when getting users", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")


@router.get(
    "/users/me",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.GetUser_Res,
    response_model_exclude_none=True    
)
async def get_current_user(db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Normal, "read"),
        ]

        payload, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="read")
        if verified is False or payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        user = payload["user"] # getting user data from payload


        stmt = select(UserModel).where(UserModel.id == user["id"])

        resp  = await db.scalars(stmt)
        existing_user = resp.unique().one()

        return existing_user

    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not found!")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when getting user", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.get(
    "/users/{id}",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.GetUser_Res,
    response_model_exclude_none=True    
)
async def get_user_by_id(id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)], Authorization: Annotated[str | None, Header()] = None):
    try: 
        if Authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")

        authorized_list=[
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Management, "read"),
            auth_utils.create_authorized_item(users_schemas.RoleEnum.DBA, "read"),
            auth_utils.create_authorized_item(users_schemas.RoleEnum.Analytics, "read"),
        ]

        _, verified = auth_utils.verify_jwt(authorization_header=Authorization, authorized_list=authorized_list, op="read")
        if verified is False:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")


        stmt = select(UserModel).where(UserModel.id == id)

        resp  = await db.scalars(stmt)
        existing_user = resp.unique().one()

        return existing_user

    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not found!")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error when getting user", error=e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown error, try again later")

@router.post(
    "/users/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=component_schemas.UserAuth_Res,
    response_model_exclude_none=True
    )
async def signup(user: component_schemas.UserSignup_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
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

        res_user = users_schemas.DescriptiveSchema(id=new_user.id, username=new_user.username, roles=new_user.roles)

        access_token = auth_utils.create_jwt(id=new_user.id, username=new_user.username, roles=new_user.roles)
        return component_schemas.UserAuth_Res(user=res_user, access_token=access_token)

    except Exception as e: 
        logger.error("Signup Error", err=e)
        await db.rollback()
        if "psycopg.errors.UniqueViolation" in str(e):
            detail_msg = "Username's already taken"
            raise HTTPException(status.HTTP_409_CONFLICT, detail=detail_msg)
        else:
            detail_msg = "An error occurred while signing up, try again later."
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=detail_msg)

@router.post(
    "/users/login",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=component_schemas.UserAuth_Res,
    response_model_exclude_none=True
)
async def login(user: component_schemas.UserLogin_Req, db: Annotated[AsyncSession, Depends(get_async_db)]):
    base_err = "User's name or password is incorrect."
    try:
        stmt = select(UserModel).where(UserModel.username == user.username) ## need to select required fields only.
        res =  await db.execute(statement=stmt)
        existing_user = res.scalar()


        if existing_user: # User exist in DB
            if auth_utils.verify_password(user.password, existing_user.password) is False: # if password is incorrect.
                raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=base_err)
            
            res_user = users_schemas.DescriptiveSchema(id=existing_user.id, username=existing_user.username, roles=existing_user.roles)
            access_token = auth_utils.create_jwt(id=existing_user.id, username=existing_user.username, roles=existing_user.roles)
            return component_schemas.UserAuth_Res(user=res_user, access_token=access_token)

        else:
            # User doesn't exist
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail=base_err)

    except exc.NoResultFound:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=base_err)
    except HTTPException as e:
        raise e
    except Exception as e:
        detail_msg = "An error occurred while loggin in, try again later."
        logger.error("Login Error", err=e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail_msg)

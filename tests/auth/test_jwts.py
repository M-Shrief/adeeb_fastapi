import pytest
import jwt
from uuid import uuid4
from datetime import datetime
###
from adeeb_fastapi.config import access_jwt_config, refresh_jwt_config
from adeeb_fastapi.database.models import JWT as JWTModel
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas import jwt as jwt_schemas
from adeeb_fastapi.utils import time as time_utils
from adeeb_fastapi.auth import jwts

@pytest.mark.asyncio
async def test_create_jwt(subtests: pytest.Subtests):
    # We need to seperate testing for our implementation of create/verify JWT
    # So we'll write the test using the package directly.
    user_id = uuid4()
    username = "Name 1"
    roles = [RoleEnum.Normal, RoleEnum.DBA]
    user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
    jti = uuid4()
    family_id= uuid4()

    access_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.ACCESS,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )
    access_model = JWTModel(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.ACCESS,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )

    refresh_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.REFRESH,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )
    refresh_model = JWTModel(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.REFRESH,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )

    with subtests.test("Correctly creating jwt, as access token from a model"):
        access_claims = await jwts.new_claims(user, model=access_model)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        payload = jwt.decode(
            jwt=token,
            key=access_jwt_config.public_key,
            algorithms=["RS256"],
        )

        # Check expiration date
        exp = payload.get("exp")
        assert exp is not None
        assert payload.get("exp") == access_claims.exp
        
        expire_timepstamp = datetime.fromtimestamp(exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds()
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.ACCESS_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.ACCESS_EXP_IN_MIN 

        payload_user = payload.get("user")
        assert payload_user is not None
        assert str(user_id) == payload_user["id"]
        assert username == payload_user["username"]
        assert access_claims.permissions == payload.get("permissions")    

    with subtests.test("Correctly creating jwt, as access token from a schema"):
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        payload = jwt.decode(
            jwt=token,
            key=access_jwt_config.public_key,
            algorithms=["RS256"],
        )

        # Check expiration date
        exp = payload.get("exp")
        assert exp is not None
        assert payload.get("exp") == access_claims.exp
        
        expire_timepstamp = datetime.fromtimestamp(exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds()
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.ACCESS_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.ACCESS_EXP_IN_MIN 

        payload_user = payload.get("user")
        assert payload_user is not None
        assert str(user_id) == payload_user["id"]
        assert username == payload_user["username"]
        assert access_claims.permissions == payload.get("permissions")    

    with subtests.test("Correctly creating jwt, as refresh token from a model"):
        refresh_claims = await jwts.new_claims(user, model=refresh_model)
        assert refresh_claims is not None
        token = await jwts.create_jwt(refresh_claims)

        payload = jwt.decode(
            jwt=token,
            key=refresh_jwt_config.public_key,
            algorithms=["RS256"],
        )

        # Check expiration date
        exp = payload.get("exp")
        assert exp is not None
        assert payload.get("exp") == refresh_claims.exp
        
        expire_timepstamp = datetime.fromtimestamp(exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds() 
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.REFRESH_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.REFRESH_EXP_IN_MIN 

    with subtests.test("Correctly creating jwt, as refresh token from a schema"):
        refresh_claims = await jwts.new_claims(user, schema=refresh_schema)
        assert refresh_claims is not None
        token = await jwts.create_jwt(refresh_claims)

        payload = jwt.decode(
            jwt=token,
            key=refresh_jwt_config.public_key,
            algorithms=["RS256"],
        )

        # Check expiration date
        exp = payload.get("exp")
        assert exp is not None
        assert payload.get("exp") == refresh_claims.exp
        
        expire_timepstamp = datetime.fromtimestamp(exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds() 
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.REFRESH_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.REFRESH_EXP_IN_MIN 



@pytest.mark.asyncio
async def test_verify_jwt(subtests: pytest.Subtests):
    user_id = uuid4()
    username = "Name 1"
    roles = [RoleEnum.Normal, RoleEnum.DBA]
    user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
    jti = uuid4()
    family_id= uuid4()

    access_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.ACCESS,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )
    refresh_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.REFRESH,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )

    with subtests.test("Correctly, Verifing JWT access token, and got the payload correctly"):
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = jwt.encode(
            payload=access_claims.model_dump(mode="json",exclude_none=True),
            key=access_jwt_config.private_key,
            algorithm="RS256"
        )

        claims, error = await jwts.verify_jwt(token)
        assert error is None, "JWT token is not verified"
        assert claims is not None, "Couldn't get payload from JWT"

        assert claims.user is not None , "Couldn't get user dict from payload"
        assert claims.user.id == user_id
        assert claims.user,username == username

        expire_timepstamp = datetime.fromtimestamp(claims.exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds() 
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.ACCESS_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.ACCESS_EXP_IN_MIN 

    with subtests.test("Correctly verifing JWT refresh token, and got the payload correctly"):
        refresh_claims = await jwts.new_claims(user, schema=refresh_schema)
        assert refresh_claims is not None
        token = jwt.encode(
            payload=refresh_claims.model_dump(mode="json",exclude_none= True),
            key=refresh_jwt_config.private_key,
            algorithm="RS256"
        )

        claims, error = await jwts.verify_jwt(token, jwt_schemas.TokenTypeEnum.REFRESH)
        assert error is None, "JWT token is not verified"
        assert claims is not None, "Couldn't get payload from JWT"

        expire_timepstamp = datetime.fromtimestamp(claims.exp)
        current_timepstamp = time_utils.Now()
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.total_seconds() 
        # we use a range to calculate passing time
        assert diff_secs > 60 * (jwts.REFRESH_EXP_IN_MIN - 2) 
        assert diff_secs < 60 * jwts.REFRESH_EXP_IN_MIN 


@pytest.mark.asyncio
async def test_new_claims(subtests: pytest.Subtests):
    user_id = uuid4()
    username = "Name 1"
    roles = [RoleEnum.Normal, RoleEnum.DBA]
    user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
    jti = uuid4()
    family_id= uuid4()

    access_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.ACCESS,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )
    access_model = JWTModel(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.ACCESS,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.ACCESS_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )

    refresh_schema = jwt_schemas.DescriptiveSchema(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.REFRESH,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )
    refresh_model = JWTModel(
        jti=jti,
        family_id=family_id,
        user_id=user_id,
        token_type=jwt_schemas.TokenTypeEnum.REFRESH,
        is_banned=False,
        used=False,
        exp=time_utils.NowWithDelta(jwts.REFRESH_EXP_IN_MIN),
        iat=time_utils.NowWithDelta(-1),
    )

    with subtests.test("Correctly creating claims for refresh token"):
        access_claims1 = await jwts.new_claims(user, model=access_model)
        assert access_claims1 is not None        
        assert access_claims1.jti == refresh_model.jti
        assert access_claims1.user is not None
        assert access_claims1.user.id  == user.id
        assert access_claims1.user.username  == user.username
        assert access_claims1.user.roles  == user.roles
        assert access_claims1.family_id == access_model.family_id
        assert access_claims1.token_type == "access"
        assert access_claims1.permissions == await jwts.create_permissions(user.roles)
        assert access_claims1.exp == int(access_model.exp.timestamp())
        assert access_claims1.iat == int(access_model.iat.timestamp())

        access_claims2 = await jwts.new_claims(user, schema=access_schema)
        assert access_claims2 is not None        
        assert access_claims2.jti == refresh_model.jti
        assert access_claims2.user is not None
        assert access_claims2.user.id  == user.id
        assert access_claims2.user.username  == user.username
        assert access_claims2.user.roles  == user.roles
        assert access_claims2.family_id == access_model.family_id
        assert access_claims2.token_type == "access"
        assert access_claims2.permissions == await jwts.create_permissions(user.roles)
        assert access_claims2.exp == int(access_model.exp.timestamp())
        assert access_claims2.iat == int(access_model.iat.timestamp())

    with subtests.test("Correctly creating claims for refresh token"):
        refresh_claims1 = await jwts.new_claims(user, model=refresh_model)
        assert refresh_claims1 is not None        
        assert refresh_claims1.jti == refresh_model.jti
        assert refresh_claims1.user is None
        assert refresh_claims1.family_id == refresh_model.family_id
        assert refresh_claims1.permissions is None
        assert refresh_claims1.token_type == "refresh"
        assert refresh_claims1.exp == int(refresh_model.exp.timestamp())
        assert refresh_claims1.iat == int(refresh_model.iat.timestamp())

        refresh_claims2 = await jwts.new_claims(user, schema=refresh_schema)
        assert refresh_claims2 is not None        
        assert refresh_claims2.jti == refresh_schema.jti
        assert refresh_claims2.user is None
        assert refresh_claims2.family_id == refresh_schema.family_id
        assert refresh_claims2.permissions is None
        assert refresh_claims2.token_type == "refresh"
        assert refresh_claims2.exp == int(refresh_schema.exp.timestamp())
        assert refresh_claims2.iat == int(refresh_schema.iat.timestamp())


@pytest.mark.asyncio
async def test_create_authorized_item():
    assert jwts.create_authorized_item(RoleEnum.Management, "read") == "Management:read"
    assert jwts.create_authorized_item(RoleEnum.Management, "write") == "Management:write"

@pytest.mark.asyncio
async def test_check_permission(subtests: pytest.Subtests):
    with subtests.test("Correctly check permissions"):
        authorized_list=[
            jwts.create_authorized_item(RoleEnum.Analytics, "read"),
            jwts.create_authorized_item(RoleEnum.DBA, "read"),
            jwts.create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            jwts.create_authorized_item(RoleEnum.Management, "read"),
        ]

        is_permitted = await jwts.check_permission(authorized_list, permissions, "read")
        assert is_permitted is True
    
    with subtests.test("correctly not permitting user without authorization"):
        authorized_list=[
            jwts.create_authorized_item(RoleEnum.Analytics, "read"),
            jwts.create_authorized_item(RoleEnum.DBA, "read"),
            jwts.create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            jwts.create_authorized_item(RoleEnum.Normal, "read"),
        ]

        is_permitted = await jwts.check_permission(authorized_list, permissions, "read")
        assert is_permitted is False
    
    with subtests.test("correctly not permitting a user without write authorization"):
        authorized_list=[
            jwts.create_authorized_item(RoleEnum.Analytics, "write"),
            jwts.create_authorized_item(RoleEnum.DBA, "write"),
            jwts.create_authorized_item(RoleEnum.Management, "write"),
        ]

        permissions=[
            jwts.create_authorized_item(RoleEnum.Normal, "read"),
            jwts.create_authorized_item(RoleEnum.DBA, "read"),
        ]

        is_permitted = await jwts.check_permission(authorized_list, permissions, "write")
        assert is_permitted is False
    
    with subtests.test("correctly not permitting banned user"):
        authorized_list=[
            jwts.create_authorized_item(RoleEnum.Analytics, "read"),
            jwts.create_authorized_item(RoleEnum.DBA, "read"),
            jwts.create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            jwts.create_authorized_item(RoleEnum.Normal, "read"),
            jwts.create_authorized_item(RoleEnum.Banned, "read"),
        ]

        is_permitted = await jwts.check_permission(authorized_list, permissions, "read")
        assert is_permitted is False
 

@pytest.mark.asyncio
async def test_check_if_banned():
    permissions1=[
        jwts.create_authorized_item(RoleEnum.Normal, "read"),
        jwts.create_authorized_item(RoleEnum.Banned, "read"),
    ]

    is_permitted = await jwts.check_if_banned(permissions1, "read")
    assert is_permitted is True

    permissions2=[
        jwts.create_authorized_item(RoleEnum.Management, "write"),
        jwts.create_authorized_item(RoleEnum.Banned, "write"),
    ]

    is_permitted = await jwts.check_if_banned(permissions2, "write")
    assert is_permitted is True


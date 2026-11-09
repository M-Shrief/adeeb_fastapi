import pytest
from fastapi import Request
from starlette.types import Scope
from uuid import uuid4
###
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas import jwt as jwt_schemas
from adeeb_fastapi.utils import time as time_utils
from adeeb_fastapi.auth import jwts, errors, utils

@pytest.mark.asyncio
async def test_check_admin_permissions(subtests: pytest.Subtests):
    with subtests.test("Correctly accepting admin permissions"):
        roles = [RoleEnum.Normal, RoleEnum.Management]
        permissions = await jwts.create_permissions(roles)

        assert await utils.check_admin_permissions(permissions, "read") is True
        assert await utils.check_admin_permissions(permissions, "write") is True
    
    with subtests.test("Correctly falsfying normal user permissions"):
        roles = [RoleEnum.Normal]
        permissions = await jwts.create_permissions(roles)

        assert await utils.check_admin_permissions(permissions, "read") is False
        assert await utils.check_admin_permissions(permissions, "write") is False
    
    with subtests.test("Correctly falsfying banned admin permissions"):
        roles = [RoleEnum.Normal, RoleEnum.Management, RoleEnum.Banned]
        permissions = await jwts.create_permissions(roles)

        assert await utils.check_admin_permissions(permissions, "read") is False
        assert await utils.check_admin_permissions(permissions, "write") is False
    

@pytest.mark.asyncio
async def test_write_ops_auth(subtests: pytest.Subtests):
    user_id = uuid4()
    username = "Name 1"
    jti = uuid4()
    family_id= uuid4()

    with subtests.test("Authorizing admin-like user to write operation"):
        scope: Scope = {"type": "http", "method": "POST"}
        request = Request(scope)
        roles = [RoleEnum.Normal, RoleEnum.DBA]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        try:
            _ = await utils.write_ops_auth(request, f"Bearer {token}")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

    with subtests.test("Not authorizing banned admin users to write operation, and throwing AuthError."):
        scope: Scope = {"type": "http", "method": "POST"}
        request = Request(scope)
        roles = [RoleEnum.Normal, RoleEnum.Management, RoleEnum.Banned]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        with pytest.raises(errors.AuthError) as err:
            _ = await utils.write_ops_auth(request, f"Bearer {token}")
            assert err.value == errors.AuthError(caused_in="middleware", reason=errors.AuthError_ReasonEnum.PERM)

    with subtests.test("Not authorizing non-admin users to write operation, and throwing AuthError."):
        scope: Scope = {"type": "http", "method": "POST"}
        request = Request(scope)
        roles = [RoleEnum.Normal]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        with pytest.raises(errors.AuthError) as err:
            _ = await utils.write_ops_auth(request, f"Bearer {token}")
            assert err.value == errors.AuthError(caused_in="middleware", reason=errors.AuthError_ReasonEnum.PERM)

    with subtests.test("Not caring about authorization in Read-only requests"):
        scope2 = {"type": "http", "method": "GET"}
        request2 = Request(scope2)
        roles = [RoleEnum.Normal]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        try:
            _ = await utils.write_ops_auth(request2)
            _ = await utils.write_ops_auth(request2, f"Bearer {token}")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")


@pytest.mark.asyncio
async def test_verifying_admin_user(subtests: pytest.Subtests):
    user_id = uuid4()
    username = "Name 1"
    jti = uuid4()
    family_id= uuid4()

    with subtests.test("Authorizing admin-like user"):
        roles = [RoleEnum.Normal, RoleEnum.DBA]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        try:
            _ = await utils.verifying_admin_user(token, "read", caused_in="service")
            _ = await utils.verifying_admin_user(token, "write", caused_in="service")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        

    with subtests.test("Not authorizing banned admin users, and throwing AuthError."):
        roles = [RoleEnum.Normal, RoleEnum.Management, RoleEnum.Banned]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_admin_user(token, "read", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)
        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_admin_user(token, "write", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)

    with subtests.test("Not authorizing non-admin users, and throwing AuthError."):
        roles = [RoleEnum.Normal]
        user = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles)
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
        access_claims = await jwts.new_claims(user, schema=access_schema)
        assert access_claims is not None
        token = await jwts.create_jwt(access_claims)

        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_admin_user(token, "read", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)
        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_admin_user(token, "write", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)


@pytest.mark.asyncio
async def test_verifying_normal_user(subtests: pytest.Subtests):
    user_id = uuid4()
    username = "Name 1"
    jti = uuid4()
    family_id= uuid4()

    with subtests.test("Authorizing normal & admin users"):
        roles1 = [RoleEnum.Normal]
        roles2 = [RoleEnum.Normal, RoleEnum.DBA]
        user1 = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles1)
        user2 = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles2)
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
        access_claims1 = await jwts.new_claims(user1, schema=access_schema)
        access_claims2 = await jwts.new_claims(user2, schema=access_schema)
        assert access_claims1 is not None
        assert access_claims2 is not None
        token1 = await jwts.create_jwt(access_claims1)
        token2 = await jwts.create_jwt(access_claims2)

        try:
            _ = await utils.verifying_normal_user(token1, "read", caused_in="service")
            _ = await utils.verifying_normal_user(token1, "write", caused_in="service")
            _ = await utils.verifying_normal_user(token2, "read", caused_in="service")
            _ = await utils.verifying_normal_user(token2, "write", caused_in="service")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")
        
    with subtests.test("Not authorizing banned users, and throwing AuthError."):
        roles1 = [RoleEnum.Normal, RoleEnum.Banned]
        roles2 = [RoleEnum.Normal, RoleEnum.DBA, RoleEnum.Banned]
        user1 = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles1)
        user2 = jwt_schemas.Claims_User(id=user_id, username=username, roles=roles2)
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
        access_claims1 = await jwts.new_claims(user1, schema=access_schema)
        access_claims2 = await jwts.new_claims(user2, schema=access_schema)
        assert access_claims1 is not None
        assert access_claims2 is not None
        token1 = await jwts.create_jwt(access_claims1)
        token2 = await jwts.create_jwt(access_claims2)

        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_normal_user(token1, "read", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)
        with pytest.raises(errors.AuthError) as err:
            _ = await utils.verifying_normal_user(token2, "write", caused_in="service")
            assert err.value == errors.AuthError(caused_in="service", reason=errors.AuthError_ReasonEnum.PERM)


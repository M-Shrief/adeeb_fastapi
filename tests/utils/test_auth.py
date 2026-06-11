import pytest
from fastapi import Request, HTTPException
from starlette.types import Scope
import jwt
from uuid import uuid4
from datetime import UTC, datetime
###
from adeeb_fastapi.config import jwt_config
from adeeb_fastapi.utils.auth import create_jwt, create_permissions, create_jwt_payload, verify_jwt, create_authorized_item, check_permission, write_ops_auth, AuthorizationError
from adeeb_fastapi.schemas.users import RoleEnum

@pytest.mark.asyncio
async def test_create_jwt():
    # We need to seperate testing for our implementation of create/verify JWT
    # So we'll write the test using the package directly.

    id = uuid4()
    username = "Name 1"
    roles = [RoleEnum.Normal, RoleEnum.DBA]
    permissions = create_permissions(roles)

    token = create_jwt(id, username, roles)

    payload = jwt.decode(
        jwt=token,
        key=jwt_config.public_key,
        algorithms=["RS256"]
    )

    # Check expiration date
    exp = payload.get("exp")
    assert exp is not None

    expire_timepstamp = datetime.fromtimestamp(exp).replace(tzinfo=None)
    current_timepstamp = datetime.now(UTC).replace(tzinfo=None)
    assert expire_timepstamp > current_timepstamp
    diff_delta = expire_timepstamp - current_timepstamp   
    diff_secs = diff_delta.seconds 
    # it's around 2 hours range, and we use a range to calculate passing time
    assert diff_secs > 17900 and diff_secs < 18100 

    user = payload.get("user")
    assert user is not None
    assert str(id) == user["id"]
    assert username == user["username"]
    assert permissions == payload.get("permissions")    


@pytest.mark.asyncio
async def test_verify_jwt(subtests: pytest.Subtests):
    # same as above, we'll seperate testing create_jwt() & verify_jwt()
    # So we'll write the test using the package directly.

    id = uuid4()
    username = "Name 1"
    roles = [RoleEnum.Normal, RoleEnum.DBA]
    permissions = create_permissions(roles)

    with subtests.test("Verifing correct JWT token, and got the payload correctly"):
        payload1 =  create_jwt_payload(id, username, roles)
        token: str = jwt.encode(
            payload=payload1,
            key=jwt_config.private_key,
            algorithm="RS256"
            )

        jwt_payload, is_verified = verify_jwt(f"Bearer {token}")
        assert is_verified is True, "JWT token is not verified"
        assert jwt_payload is not None, "Couldn't get payload from JWT"

        user = jwt_payload.get("user")
        assert user is not None , "Couldn't get user dict from payload"
        assert str(id) == user["id"]
        assert username == user["username"]
        assert permissions == jwt_payload.get("permissions")    

        # Check expiration date
        exp = jwt_payload.get("exp")
        assert exp is not None
        expire_timepstamp = datetime.fromtimestamp(exp).replace(tzinfo=None)
        current_timepstamp = datetime.now(UTC).replace(tzinfo=None)
        assert expire_timepstamp > current_timepstamp
        diff_delta = expire_timepstamp - current_timepstamp   
        diff_secs = diff_delta.seconds 
        assert diff_secs > 17900 and diff_secs < 18100 

    with subtests.test("Verifing expired JWT token"):
        payload1 =  create_jwt_payload(id, username, roles, 0)
        token: str = jwt.encode(
            payload=payload1,
            key=jwt_config.private_key,
            algorithm="RS256"
            )
        jwt_payload, is_verified = verify_jwt(f"Bearer {token}")
        assert is_verified is False, "JWT token is verified"
        assert jwt_payload is None, "payload is not None"

    with subtests.test("Verifing incorrect JWT token"):
        token = "Bearer eyJhbahaOisfsaI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiMDk1NzE0ZDgtMzYyMi00NmFhLWIzNTgtMTUwZGIwYmY0Y2UyIiwidXNlcm5h...qHawhh2WZgFCJ4X4RBA_Z29eQSb3NsjFoLL2Z5xDqoUCgdlXNijjtX16xsVoW5HC9w8xZ_79bmjMkYuyToVNd7Mt395AbyIhXvHKQC4WnFP1qs8mo3IQzo"

        jwt_payload, is_verified = verify_jwt(f"Bearer {token}")
        assert is_verified is False, "JWT token is verifiy incorrectly"
        assert jwt_payload is None, "payload is not None"

@pytest.mark.asyncio
async def test_check_permission(subtests: pytest.Subtests):

    with subtests.test("Correctly check permissions"):
        authorized_list=[
            create_authorized_item(RoleEnum.Analytics, "read"),
            create_authorized_item(RoleEnum.DBA, "read"),
            create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            create_authorized_item(RoleEnum.Management, "read"),
        ]

        is_permitted = check_permission(authorized_list, permissions, "read")
        assert is_permitted is True
    
    with subtests.test("correctly not permitting user without authorization"):
        authorized_list=[
            create_authorized_item(RoleEnum.Analytics, "read"),
            create_authorized_item(RoleEnum.DBA, "read"),
            create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            create_authorized_item(RoleEnum.Normal, "read"),
        ]

        is_permitted = check_permission(authorized_list, permissions, "read")
        assert is_permitted is False
    
    with subtests.test("correctly not permitting a user without write authorization"):
        authorized_list=[
            create_authorized_item(RoleEnum.Analytics, "write"),
            create_authorized_item(RoleEnum.DBA, "write"),
            create_authorized_item(RoleEnum.Management, "write"),
        ]

        permissions=[
            create_authorized_item(RoleEnum.Normal, "read"),
            create_authorized_item(RoleEnum.DBA, "read"),
        ]

        is_permitted = check_permission(authorized_list, permissions, "write")
        assert is_permitted is False
    
    with subtests.test("correctly not permitting banned user"):
        authorized_list=[
            create_authorized_item(RoleEnum.Analytics, "read"),
            create_authorized_item(RoleEnum.DBA, "read"),
            create_authorized_item(RoleEnum.Management, "read"),
        ]

        permissions=[
            create_authorized_item(RoleEnum.Normal, "read"),
            create_authorized_item(RoleEnum.BANNED, "read"),
        ]

        is_permitted = check_permission(authorized_list, permissions, "read")
        assert is_permitted is False
 
    
@pytest.mark.asyncio
async def test_write_ops_auth(subtests: pytest.Subtests):
    id = uuid4()
    username = "Name 1"

    scope: Scope = {"type": "http", "method": "POST"}
    request = Request(scope)

    with subtests.test("Authorizing admin-like user to write operation"):
        roles = [RoleEnum.Normal, RoleEnum.DBA]
        token = create_jwt(id, username, roles)

        try:
            _ = await write_ops_auth(request, f"Bearer {token}")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

    with subtests.test("Not authorizing non-admin users to write operation, and throwing Authorization error."):
        roles = [RoleEnum.Normal]
        token = create_jwt(id, username, roles)

        with pytest.raises(HTTPException) as err:
            _ = await write_ops_auth(request, f"Bearer {token}")
        assert err.value == AuthorizationError

    with subtests.test("Not caring about authorization in Read-only requests"):
        scope2 = {"type": "http", "method": "GET"}
        request2 = Request(scope2)
        roles = [RoleEnum.Normal]
        token = create_jwt(id, username, roles, exp_hours=0)

        try:
            _ = await write_ops_auth(request2)
            _ = await write_ops_auth(request2, f"Bearer {token}")
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

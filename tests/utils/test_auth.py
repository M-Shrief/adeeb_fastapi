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


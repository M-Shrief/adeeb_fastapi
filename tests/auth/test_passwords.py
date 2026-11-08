import pytest
import bcrypt
###
from adeeb_fastapi.auth.passwords import hash_password, verify_password

@pytest.mark.asyncio
async def test_hash_password():
    password = "P@ssword1"
    hashed_password = await hash_password(password)

    is_correctly_hashed = bcrypt.checkpw(password.encode(), hashed_password.encode())

    assert is_correctly_hashed is True

@pytest.mark.asyncio
async def test_verify_password():
    password = "P@ssword1"
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    assert await verify_password(password, hashed_password) is True
    assert await verify_password("p@ssword1", hashed_password) is False
    assert await verify_password("P@ssword", hashed_password) is False
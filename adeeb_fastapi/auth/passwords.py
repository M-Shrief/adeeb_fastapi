import bcrypt


async def hash_password(password: str) -> str:
    hashed_password: bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    return hashed_password.decode()

async def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

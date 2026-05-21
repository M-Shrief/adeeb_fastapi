from typing import Any
from sqlalchemy.engine import URL , create_engine
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from collections.abc import AsyncGenerator, Generator
#####
from adeeb_fastapi.config import DB

db_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB.get('user'),
    password=DB.get('password'),
    host=DB.get('host'),
    database=DB.get('name'),
    port=DB.get('port')
)


async_engine: AsyncEngine = create_async_engine(db_url)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=async_engine)

# FastAPI's dependency with yield: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/
async def get_async_db() -> AsyncGenerator[AsyncSession, Any]:
    db: AsyncSession = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


sync_engine = create_engine(db_url)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# FastAPI's dependency with yield: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/
def get_sync_db() -> Generator[Session, Any]:
    db: Session = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

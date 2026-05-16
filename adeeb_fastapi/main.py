from fastapi import FastAPI, status
from scalar_fastapi import get_scalar_api_reference # pyright:ignore[reportUnknownVariableType]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
###
from adeeb_fastapi.database.index import async_engine
from adeeb_fastapi.database.models import Base
# Components
from adeeb_fastapi.components.users.router import router as users_router
from adeeb_fastapi.components.adeebs.router import router as adeebs_router
from adeeb_fastapi.components.poems.router import router as poems_router
from adeeb_fastapi.components.chosen_verses.router import router as chosen_verses_router
from adeeb_fastapi.components.prose_qoutes.router import router as prose_qoutes_router
# Schemas
from adeeb_fastapi.schemas import api  as api_schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
   lifespan=lifespan,
    title="Adeeb FastAPI",
    description="An Iteration for Adeeb's RESTful API using Python, FastAPI and Postgres.",
    summary="An Iteration for Adeeb's RESTful API using Python",
    version="0.1.0",
    # docs_url="/docs",
    # redoc_url="/redoc"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=5
)

@app.get("/", status_code=status.HTTP_200_OK)
async def homepage():    
    return {
            "title": app.title,
            "description": app.description,
            "version": app.version,
            "Swagger-documentation_url": app.docs_url,
            "Redoc-documentation_url": app.redoc_url,
            "Scalar-documentation_url": "/scalar"            
        }

@app.get(
    "/scalar",
    include_in_schema=False,
    description="Scalar Modern API Client and Reference, check on https://github.com/scalar/scalar"
    )
async def scalar_html() :
    if app.openapi_url is None:
        return "Not Available"

    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

@app.get("/ping",status_code=status.HTTP_200_OK, response_model=api_schemas.BaseRes)
async def ping():    
    return api_schemas.BaseRes(message="pong")

### Adding API routes
app.include_router(users_router, prefix="/api")
app.include_router(adeebs_router, prefix="/api")
app.include_router(poems_router, prefix="/api")
app.include_router(chosen_verses_router, prefix="/api")
app.include_router(prose_qoutes_router, prefix="/api")

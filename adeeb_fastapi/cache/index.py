from pydantic import BaseModel
from glide import  GlideClient, GlideClientConfiguration, NodeAddress, ServerCredentials, AdvancedGlideClientConfiguration, ExpirySet, ExpiryType, CompressionConfiguration, CompressionBackend
from collections.abc import AsyncGenerator
from typing import Any
from json import loads
from uuid import UUID
###
from adeeb_fastapi.config import cache_config

async def get_async_cache()  -> AsyncGenerator[GlideClient, Any]:
    cache = await GlideClient.create(
        config=GlideClientConfiguration(
            addresses=[
                NodeAddress(cache_config.host, cache_config.port)
            ],
            credentials=ServerCredentials(password=cache_config.password),
            advanced_config=AdvancedGlideClientConfiguration(connection_timeout=1000),
            compression=CompressionConfiguration(
                enabled=True,
                backend=CompressionBackend.ZSTD,
                compression_level=3,
                min_compression_size= 1024 * 3 # min 3 kb
            ),
            request_timeout=5000,
            use_tls=False,
        )
    )
    try:
        yield cache
    finally:
        await cache.close()

# Reusable functions to reduce boilerplate

async def cache_get(key: str, client: GlideClient):
    try:
        result = await client.get(key)
        if result is None:
            return None
        obj: dict[str, Any] = loads(result.decode('utf-8'))
        return obj
    except Exception:
        return None

async def cache_set(key: str, value: BaseModel, client: GlideClient):
    try:
        _ = await client.set(
            key=key,
            value=value.model_dump_json(indent=0,exclude_none=True, exclude_unset=True), # set indent=0 to decrease the string size.
            expiry=ExpirySet(ExpiryType.SEC, 60 * 15)
        )
    
        return None
    except Exception:
        return None

def format_key_by_id(prefix: str, id: UUID):
    """Format key for a row in the database, using the individule name of the entity - adeebs --> adeeb,
    and it's id"""
    return f"{prefix}:{id}"

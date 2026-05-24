from pydantic import BaseModel
from glide import  GlideClient, GlideClientConfiguration, NodeAddress, ServerCredentials, AdvancedGlideClientConfiguration, ExpirySet, ExpiryType, CompressionConfiguration, CompressionBackend
from collections.abc import AsyncGenerator
from typing import Any
from json import loads
from uuid import UUID
###
from adeeb_fastapi.config import CACHE

async def get_async_cache()  -> AsyncGenerator[GlideClient, Any]:
    cache = await GlideClient.create(
        config=GlideClientConfiguration(
            addresses=[
                NodeAddress(CACHE.get("host"), CACHE.get("port"))
            ],
            credentials=ServerCredentials(password=CACHE.get("password")),
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

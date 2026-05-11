import logging
import structlog
###
# from oss_archive.config import ENV

proccessors_configs = []

# if ENV == "dev": # Prettier logs for development
#     proccessors_configs = [
#         structlog.contextvars.merge_contextvars,
#         structlog.processors.add_log_level,
#         structlog.processors.StackInfoRenderer(),
#         structlog.dev.set_exc_info,
#         structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
#         structlog.dev.ConsoleRenderer(),
#     ]
# else: # JSON format, if it's in production
proccessors_configs = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.dev.set_exc_info,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    structlog.processors.JSONRenderer(),
]

structlog.configure(
    processors=proccessors_configs,
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger: structlog.ReturnLogger = structlog.get_logger() # pyright: ignore[reportAny]


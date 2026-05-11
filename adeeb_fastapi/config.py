from dotenv import dotenv_values
from typing import TypedDict

__env = dotenv_values(".env")

ENV = __env.get("ENV") or "dev"

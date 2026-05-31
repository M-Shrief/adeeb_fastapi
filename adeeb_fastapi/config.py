from dotenv import dotenv_values
from typing import TypedDict

__env = dotenv_values(".env")

ENV = __env.get("ENV") or "dev"

# Database
class DatabaseConfigType(TypedDict):
    user: str
    password: str
    host: str
    port: int
    name: str
    url: str
    conn_str: str

db_port = __env.get("DB_PORT")

DB = DatabaseConfigType(
    user= __env.get("DB_USER") or "postgres",
    password= __env.get("DB_PASSWORD") or "postgres",
    host= __env.get("DB_HOST") or "localhost",
    port= int(db_port) if db_port is not None else 5432,
    name= __env.get("DB_NAME") or "adeeb_db",
    url= F"postgresql://{__env.get("DB_USER")}:{__env.get("DB_PASSWORD")}@{__env.get("DB_HOST")}:{__env.get("DB_PORT")}/{__env.get("DB_NAME")}",
    conn_str=  F"host={__env.get("DB_HOST")} port={__env.get("DB_PORT")} user={__env.get("DB_USER")} dbname={__env.get("DB_NAME")} password={__env.get("DB_PASSWORD")} sslmode=disable"        
    )

class CacheConfigType(TypedDict):
    host: str
    password: str
    port: int

cache_port = __env.get("DB_VALKEY_PORTPORT")

CACHE = CacheConfigType(
    host= __env.get("VALKEY_HOST") or "localhost",
    password= __env.get("VALKEY_PASSWORD") or "postgres",
    port= int(cache_port) if cache_port is not None else 6379,
)

class JWTKeysType(TypedDict):
    private: str
    public: str

private_key_path = __env.get("JWT_PRIVATE")
public_key_path = __env.get("JWT_PUBLIC")

JWTKeys = JWTKeysType(
    private=open(private_key_path if private_key_path is not None else "jwt_private_rsa256.key").read(),
    public=open(public_key_path if public_key_path is not None else "jwt_public_rsa256.key").read(),
)
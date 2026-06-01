from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Note: Use .model_validate({}) to prevent Basedpyright errros when initializing the class"""
    model_config = SettingsConfigDict(
        env_file='.env',  # path of .env
        env_file_encoding='utf-8',
        env_prefix="DB_", #prefix for everey field.
        extra="ignore" # ignore other ENV so that we can modularize its use.
    )
    user: str
    password: str
    host: str
    port: int
    name: str

    @computed_field
    @property
    def url(self)-> str:
        return F"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @computed_field
    @property
    def conn_str(self)->str:
        return F"host={self.host} port={self.port} user={self.user} dbname={self.name} password={self.password} sslmode=disable"

db_config = DatabaseConfig.model_validate({})

class CacheConfig(BaseSettings):
    """Note: Use .model_validate({}) to prevent Basedpyright errros when initializing the class"""
    model_config = SettingsConfigDict(
        env_file='.env',  # path of .env
        env_file_encoding='utf-8',
        env_prefix="VALKEY_", #prefix for everey field.
        extra="ignore" # ignore other ENV so that we can modularize its use.
    )

    host: str
    password: str
    port: int

cache_config = CacheConfig.model_validate({})

class JWTConfig(BaseSettings):
    """Note: Use .model_validate({}) to prevent Basedpyright errros when initializing the class"""
    model_config = SettingsConfigDict(
        env_file='.env',  # path of .env
        env_file_encoding='utf-8',
        env_prefix="JWT_", #prefix for everey field.
        extra="ignore" # ignore other ENV so that we can modularize its use.
    )

    private_path: str
    public_path: str

    @computed_field
    @property
    def private_key(self)->str:
        return open(self.private_path).read()

    @computed_field
    @property
    def public_key(self)->str:
        return open(self.public_path).read()

jwt_config = JWTConfig.model_validate({})

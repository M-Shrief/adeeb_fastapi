from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import DateTime, Enum, ARRAY, String, text, Boolean, ForeignKey
from datetime import datetime
# from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID
###
from adeeb_fastapi.schemas.general import TimePeriodEnum,  OutfitTypeEnum
from adeeb_fastapi.schemas.users import RoleEnum
from adeeb_fastapi.schemas.orders import OrderStatusEnum


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

class Timestamps():
    """Entity Timestamps"""
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))


# Enums
roles_enum = Enum(RoleEnum.Analytics, RoleEnum.Normal, RoleEnum.DBA, RoleEnum.Management, RoleEnum.BANNED, name="roles_enum")
time_period_enum = Enum(TimePeriodEnum.JAHLI, TimePeriodEnum.AMOEI, TimePeriodEnum.ABASI, TimePeriodEnum.ANDALUSI, TimePeriodEnum.TURKISH_ERA, TimePeriodEnum.MODERN, TimePeriodEnum.UNDEFINED, name="time_period_enum")
outfit_type_enum = Enum(OutfitTypeEnum.TSHIRT_7, OutfitTypeEnum.TSHIRT_HALF, OutfitTypeEnum.TSHIRT_POLO,OutfitTypeEnum.SWEETSHIRT, OutfitTypeEnum.JACKET, OutfitTypeEnum.PULLOVER, name="outfit_type_enum")
order_status_enum = Enum(OrderStatusEnum.IN_PROGRESS, OrderStatusEnum.COMPLETED, OrderStatusEnum.ABORTED, name="order_status_enum")

class User(Timestamps, Base):
    __tablename__: str = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String(length=256), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(length=256), nullable=False)
    roles: Mapped[list[RoleEnum]] = mapped_column(ARRAY(Enum(RoleEnum, name="roles_enum", native_enum=True)), nullable=False, default=[RoleEnum.Normal])

    orders: Mapped[list[Order]] = relationship(back_populates="user")


class Adeeb(Timestamps, Base):
    __tablename__: str = "adeebs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(length=256), unique=True, nullable=True)
    time_period: Mapped[TimePeriodEnum] = mapped_column(Enum(TimePeriodEnum, name="time_period_enum", native_enum=True), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(length=1024), nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)

    ### Relationships
    poems: Mapped[list[Poem]] = relationship(back_populates="adeeb")
    chosen_verses: Mapped[list[ChosenVerses]] = relationship(back_populates="adeeb")
    prose_qoutes: Mapped[list[ProseQoute]] = relationship(back_populates="adeeb")

class Poem(Timestamps, Base):
    __tablename__: str = "poems"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    intro: Mapped[str | None] = mapped_column(String(length=256), unique=True, nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)
    # instead of making a custom type for verses, 
    # we'll use an array and add another field to know if it's couplet or not
    # and in this way we support other poems that uses lines rather than couplet
    verses: Mapped[list[str]] = mapped_column(ARRAY(String(length=256)), default=[])
    is_couplet: Mapped[bool] = mapped_column(Boolean(), default=True)

    ### Relationships
    adeeb_id: Mapped[UUID] = mapped_column(ForeignKey("adeebs.id"), nullable=False)
    adeeb: Mapped[Adeeb] = relationship(back_populates="poems")

    chosen_verses: Mapped[list[ChosenVerses]] = relationship(back_populates="poem")


class ChosenVerses(Timestamps, Base):
    __tablename__: str = "chosen_verses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(length=256)), default=[])
    verses: Mapped[list[str]] = mapped_column(ARRAY(String(length=256)), default=[])
    is_couplet: Mapped[bool] = mapped_column(Boolean(), default=True)
    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)

    ### Relationships
    adeeb_id: Mapped[UUID] = mapped_column(ForeignKey("adeebs.id"), nullable=False)
    adeeb: Mapped[Adeeb] = relationship(back_populates="chosen_verses")

    poem_id: Mapped[UUID] = mapped_column(ForeignKey("poems.id"), nullable=False)
    poem: Mapped[Poem] = relationship(back_populates="chosen_verses")


class ProseQoute(Timestamps, Base):
    __tablename__: str = "prose_qoutes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(length=256)), default=[])
    qoute: Mapped[str] = mapped_column(String(length=512), nullable=False)
    source: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)

    ### Relationships
    adeeb_id: Mapped[UUID] = mapped_column(ForeignKey("adeebs.id"), nullable=False)
    adeeb: Mapped[Adeeb] = relationship(back_populates="prose_qoutes")

class Order(Timestamps, Base):
    __tablename__: str = "orders"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)

    name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    phone: Mapped[str] = mapped_column(String(length=128), nullable=False)
    address: Mapped[str] = mapped_column(String(length=256), nullable=False)

    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)
    delivery_schedule: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True, default=None)
    is_updateable: Mapped[bool] = mapped_column(Boolean(), default=True)
    # delete this fields, and replace them with status as ENUM("In progress", "Aborted", "Completed")
    status: Mapped[OrderStatusEnum] = mapped_column(Enum(OrderStatusEnum, name="order_status_enum", native_enum=True), nullable=False, default=OrderStatusEnum.IN_PROGRESS)

    ### Relationships
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)
    user: Mapped[User] = relationship(back_populates="orders")

    prints: Mapped[list[Print]] = relationship(back_populates="order")

class Print(Base):
    __tablename__: str = "prints"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)

    font_type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    font_color: Mapped[str] = mapped_column(String(length=64), nullable=False)
    outfit_color: Mapped[str] = mapped_column(String(length=64), nullable=False)
    outfit_type: Mapped[OutfitTypeEnum] = mapped_column(Enum(OutfitTypeEnum, name="outfit_type_enum", native_enum=True), nullable=False)

    # Foreign ids to know from where did the customer chose his print, for analytics and such
    poem_id: Mapped[UUID | None] = mapped_column(ForeignKey("poems.id"), nullable=True, default=None)
    chosen_verse_id: Mapped[UUID | None] = mapped_column(ForeignKey("chosen_verses.id"), nullable=True, default=None)
    prose_qoute_id: Mapped[UUID | None] = mapped_column(ForeignKey("prose_qoutes.id"), nullable=True, default=None)

    # Print's Text    
    qoute: Mapped[str | None] = mapped_column(String(length=512), nullable=True, default=None)
    verses: Mapped[list[str] | None] = mapped_column(ARRAY(String(length=256)), nullable=True, default=None)
    is_couplet: Mapped[bool | None] = mapped_column(Boolean(), nullable=True, default=None)

    ### Relationships
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    order: Mapped[Order] = relationship(back_populates="prints")

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)
    user: Mapped[User] = relationship()

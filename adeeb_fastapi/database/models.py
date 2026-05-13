from os import posix_openpt
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, validates
from sqlalchemy import Table, Column, DateTime, Enum, ARRAY, String, text, SmallInteger, Boolean, ForeignKey
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID
###
from adeeb_fastapi.schemas.general import TimePeriodEnum


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

class Timestamps():
    """Entity Timestamps"""
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))


# Enums
time_period_enum = Enum('جاهلي', 'أموي', 'عباسي', 'أندلسي', 'عثماني ومملوكي', 'متأخر وحديث', 'غير محدد', name="time_period_enum")



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


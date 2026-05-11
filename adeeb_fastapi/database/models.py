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

class Timestamps(Base):
    # Entity Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))


# Enums
time_period_enum = Enum('جاهلي', 'أموي', 'عباسي', 'أندلسي', 'عثماني ومملوكي', 'متأخر وحديث', 'غير محدد', name="time_period_enum")

class Poet(Timestamps, Base):
    __tablename__: str = "poets"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), server_default=text("gen_random_uuid()"), primary_key=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(length=256), nullable=True)
    time_period: Mapped[TimePeriodEnum] = mapped_column(Enum(TimePeriodEnum, name="time_period_enum", native_enum=True), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(length=1024), nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean(), default=False)


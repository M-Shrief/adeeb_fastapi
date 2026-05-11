
from pydantic import Field, BaseModel
from datetime import datetime
from typing import Annotated
from uuid import UUID
from enum import Enum


# General Fields
IDField = Annotated[UUID, Field()]
ReviewedField = Annotated[bool, Field(default=False)]
ReviewedField_Optional= Annotated[bool | None, Field(default=None)]
CreatedAtField = Annotated[datetime, Field()]
UpdatedAtField = Annotated[datetime, Field()]

# Relations' fields
AdeebIDField = Annotated[UUID, Field()]
AdeebIDField_Optional = Annotated[UUID | None, Field(default=None)]
PoemIDField = Annotated[UUID, Field()]
PoemIDField_Optional = Annotated[UUID | None, Field(default=None)]

# Enums
class TimePeriodEnum(str, Enum):
    UNDEFINED = "غير محدد"
    JAHLI = "جاهلي"
    AMOEI = "أموي"
    ABASI = "عباسي"
    ANDALUSI = "أندلسي"
    TURKISH_ERA = "عثماني ومملوكي"
    MODERN = "حديث"

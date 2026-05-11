
from pydantic import Field, BaseModel
from datetime import datetime
from typing import Annotated
from uuid import UUID
from enum import Enum

class TimePeriodEnum(str, Enum):
    UNDEFINED = "غير محدد"
    JAHLI = "جاهلي"
    AMOEI = "أموي"
    ABASI = "عباسي"
    ANDALUSI = "أندلسي"
    TURKISH_ERA = "عثماني ومملوكي"
    MODERN = "حديث"

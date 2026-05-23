from pydantic import Field, BaseModel
from typing import Annotated
from datetime import datetime
from enum import Enum
### 
from adeeb_fastapi.schemas import general

NameField = Annotated[str, Field(max_length=128)]
NameField_Optional = Annotated[str | None, Field(default=None, max_length=128)]

PhoneField = Annotated[str, Field(max_length=128)]
PhoneField_Optional = Annotated[str | None, Field(default=None, max_length=128)]

AddressField = Annotated[str, Field(max_length=256)]
AddressField_Optional = Annotated[str | None, Field(default=None, max_length=256)]

IsUpdateableField = Annotated[bool, Field(default=False)]
IsUpdateableField_Optional= Annotated[bool | None, Field(default=None)]

DeliveryScheduleField_Optional=   Annotated[datetime | None, Field(default=None, examples=["2026-05-30"])]
class OrderStatusEnum(str, Enum):
    IN_PROGRESS = "in progress"
    ABORTED = "aborted"
    COMPLETED = "completed"

StatusField = Annotated[OrderStatusEnum, Field(default=OrderStatusEnum.IN_PROGRESS)]
StatusField_Optional = Annotated[OrderStatusEnum | None, Field(default=None)]
class FullSchema(BaseModel):
    id: general.IDField
    name: NameField
    phone: PhoneField
    address: AddressField
    reviewed: general.ReviewedField
    is_updateable: IsUpdateableField
    status: StatusField
    delivery_schedule: DeliveryScheduleField_Optional
    created_at: general.CreatedAtField
    updated_at: general.UpdatedAtField
    # Relations
    user_id: general.UserIDField_Optional

class DescriptiveSchema(BaseModel):
    id: general.IDField
    name: NameField
    phone: PhoneField
    address: AddressField
    is_updateable: IsUpdateableField
    status: StatusField
    delivery_schedule: DeliveryScheduleField_Optional
    # Relations
    user_id: general.UserIDField_Optional

class MinimalSchema(BaseModel):
    id: general.IDField
    name: NameField
    status: StatusField
    # Relations
    user_id: general.UserIDField_Optional

from pydantic import Field, BaseModel
from typing import Annotated
from datetime import datetime
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

IsAbortedField = Annotated[bool, Field(default=False)]
IsAbortedField_Optional= Annotated[bool | None, Field(default=None)]

IsCompletedField = Annotated[bool, Field(default=False)]
IsCompletedField_Optional= Annotated[bool | None, Field(default=None)]

DeliveryScheduleField_Optional=   Annotated[datetime | None, Field(default=None, examples=["2026-05-30"])]


class FullSchema(BaseModel):
    id: general.IDField
    name: NameField
    phone: PhoneField
    address: AddressField
    reviewed: general.ReviewedField
    is_updateable: IsUpdateableField
    is_aborted: IsAbortedField
    is_completed: IsCompletedField
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
    delivery_schedule: DeliveryScheduleField_Optional
    # Relations
    user_id: general.UserIDField_Optional

class MinimalSchema(BaseModel):
    id: general.IDField
    name: NameField
    delivery_schedule: DeliveryScheduleField_Optional
    # Relations
    user_id: general.UserIDField_Optional

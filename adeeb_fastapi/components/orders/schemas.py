
from pydantic import BaseModel, Field
from typing import Annotated
from datetime import timedelta
###
from adeeb_fastapi.schemas import general, api, orders, prints, prose_qoutes

DELIVERY_AFTER = timedelta(days=7)

class PrintItem_Req(BaseModel):
    font_type: prints.FontTypeField
    font_color: prints.FontColorField
    outfit_color: prints.OutfitColorField
    outfit_type: prints.OutfitTypeField
    qoute: prose_qoutes.QouteField_Optional
    verses: general.VersesField_Optional
    is_couplet: general.IsCoupletField_Optional
    # Relations
    poem_id: general.PoemIDField_Optional
    chosen_verse_id: general.ChosenVerseIDField_Optional
    prose_qoute_id: general.ProseQouteIDField_Optional

class PrintItem_Res(PrintItem_Req):
    id: general.IDField


class GetOrders_Res(orders.FullSchema):
    prints: list[PrintItem_Res]

class GetOrder_Res(orders.DescriptiveSchema):
    prints: list[PrintItem_Res]

class CreateOneOrder_Req(BaseModel):
    # for Orders Table
    name: orders.NameField
    phone: orders.PhoneField
    address: orders.AddressField
    delivery_schedule: orders.DeliveryScheduleField_Optional
    ## Relations
    user_id: general.UserIDField_Optional

    # For prints table
    prints: list[PrintItem_Req]

class CreateOneOrder_Res(GetOrder_Res):
    pass


class CreateManyOrder_Res(BaseModel):
    created_items: Annotated[list[CreateOneOrder_Res], Field(default=[])]
    invalid_items: Annotated[list[api.InvalidDataFieldType[CreateOneOrder_Req]], Field(default=[])]
    success_count: Annotated[int, Field(default=0)]

class UpdateOrder_Req(BaseModel):
    name: orders.NameField_Optional
    phone: orders.PhoneField_Optional
    address: orders.AddressField_Optional
    reviewed: general.ReviewedField_Optional
    is_updateable: orders.IsUpdateableField_Optional
    is_aborted: orders.IsAbortedField_Optional
    is_completed: orders.IsCompletedField_Optional
    delivery_schedule: orders.DeliveryScheduleField_Optional
    # Relations
    user_id: general.UserIDField_Optional

class UpdatePrint_Req(BaseModel):
    font_type: prints.FontTypeField_Optional
    font_color: prints.FontColorField_Optional
    outfit_color: prints.OutfitColorField_Optional
    outfit_type: prints.OutfitTypeField_Optional
    # We don't udpate Prints text or relations,
    # if they don't want it they delete it as a whole, and add another print one with another text, relations...etc


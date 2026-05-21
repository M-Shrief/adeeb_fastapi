from pydantic import Field, BaseModel
from typing import Annotated
### 
from adeeb_fastapi.schemas import general, prose_qoutes

FontTypeField = Annotated[str, Field(max_length=64)]
FontTypeField_Optional = Annotated[str | None, Field(default=None, max_length=64)]

FontColorField = Annotated[str, Field(max_length=64)]
FontColorField_Optional = Annotated[str | None, Field(default=None, max_length=64)]

OutfitColorField = Annotated[str, Field(max_length=64)]
OutfitColorField_Optional = Annotated[str | None, Field(default=None, max_length=64)]

OutfitTypeField = Annotated[general.OutfitTypeEnum, Field(max_length=64)]
OutfitTypeField_Optional = Annotated[general.OutfitTypeEnum | None, Field(default=None, max_length=64)]


class FullSchema(BaseModel):
    id: general.IDField

    font_type: FontTypeField
    font_color: FontColorField
    outfit_color: OutfitColorField
    outfit_type: OutfitTypeField
    qoute: prose_qoutes.QouteField_Optional
    verses: general.VersesField_Optional
    is_couplet: general.IsCoupletField_Optional

    # Relations
    order_id: general.OrderIDField
    user_id: general.UserIDField_Optional
    poem_id: general.PoemIDField_Optional
    chosen_verse_id: general.ChosenVerseIDField_Optional
    prose_qoute_id: general.ProseQouteIDField_Optional


class DescriptiveSchema(BaseModel):
    id: general.IDField

    font_type: FontTypeField
    font_color: FontColorField
    outfit_color: OutfitColorField
    outfit_type: OutfitTypeField
    qoute: prose_qoutes.QouteField_Optional
    verses: general.VersesField_Optional
    is_couplet: general.IsCoupletField_Optional

    # Relations
    order_id: general.OrderIDField
    user_id: general.UserIDField_Optional
    poem_id: general.PoemIDField_Optional
    chosen_verse_id: general.ChosenVerseIDField_Optional
    prose_qoute_id: general.ProseQouteIDField_Optional


class MinimalSchema(BaseModel):
    id: general.IDField
    font_type: FontTypeField
    font_color: FontColorField
    outfit_color: OutfitColorField
    outfit_type: OutfitTypeField
    qoute: prose_qoutes.QouteField_Optional
    verses: general.VersesField_Optional
    is_couplet: general.IsCoupletField_Optional


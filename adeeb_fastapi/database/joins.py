"""
JOIN statements corressponding to every model's MinimalSchema
Used like:

from adeeb_fastapi.database import joins
route():
    ...
    stmt = select(AdeebModel).where(AdeebModel.id == id)
    adeeb_stmt = stmt.options(joins.poems_to_adeeb).options(joins.chosen_verses_to_adeeb)
    ...
"""

from adeeb_fastapi.database.models import Adeeb as AdeebModel, Poem as PoemModel, ChosenVerses as ChosenVersesModel, ProseQoute as ProseQouteModel
from sqlalchemy.orm import joinedload, load_only

#options(joinedload(CategoryModel.owners)).options(joinedload(CategoryModel.main_oss).load_only(OSSModel.id, OSSModel.fullname, OSSModel.priority, OSSModel.is_mirrored))



adeebs_to_poems = joinedload(PoemModel.adeeb).load_only(AdeebModel.id, AdeebModel.name)
adeebs_to_chosen_verses = joinedload(ChosenVersesModel.adeeb).load_only(AdeebModel.id, AdeebModel.name)
adeebs_to_prose_qoutes = joinedload(ProseQouteModel.adeeb).load_only(AdeebModel.id, AdeebModel.name)

poems_to_adeeb = joinedload(AdeebModel.poems).load_only(PoemModel.id, PoemModel.intro)
poems_to_chosen_verses = joinedload(ChosenVersesModel.poem).load_only(PoemModel.id, PoemModel.intro)

chosen_verses_to_poem = joinedload(PoemModel.chosen_verses).load_only(ChosenVersesModel.id, ChosenVersesModel.verses)
chosen_verses_to_adeeb = joinedload(AdeebModel.chosen_verses).load_only(ChosenVersesModel.id, ChosenVersesModel.verses)

prose_qoutes_to_adeeb = joinedload(AdeebModel.prose_qoutes).load_only(ProseQouteModel.id, ProseQouteModel.qoute)


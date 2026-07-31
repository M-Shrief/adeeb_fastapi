from typing import  Any
from uuid import UUID
###



def check_order_ownership(user_id: UUID | None, jwt_payload: dict[str, Any]):
    if user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
        return False
    else: # check if it's the same user. if it's not,  it return False
        user = jwt_payload["user"]
        if str(user_id) != user["id"]:
            return False
        else: # if it's owned by the user
            return True


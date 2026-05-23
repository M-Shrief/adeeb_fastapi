from typing import Literal,  Any
###
from adeeb_fastapi.utils import auth as auth_utils
from adeeb_fastapi.database.models import Order as OrderModel
from adeeb_fastapi.schemas.users import RoleEnum

def check_adminstration(permissions: list[str], op: Literal["write", "read"]):
    authorized_list=[
        auth_utils.create_authorized_item(RoleEnum.Analytics, op),
        auth_utils.create_authorized_item(RoleEnum.DBA, op),
        auth_utils.create_authorized_item(RoleEnum.Management, op),
    ]
    is_administrator = auth_utils.check_permission(authorized_list, permissions, op)
    
    return is_administrator


def check_order_ownership(order: OrderModel, jwt_payload: dict[str, Any]):
    if order.user_id is None: # if there's no user_id, then it's not a registered user, so no need to compare ids
        return False
    else: # check if it's the same user. if it's not,  it return False
        user = jwt_payload["user"]
        if str(order.user_id) != user["id"]:
            return False
        else: # if it's owned by the user
            return True


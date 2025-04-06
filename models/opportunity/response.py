from typing import (
    Any,
    Self,
)
import mongoengine as mongo

from ..user import User
from .form import OpportunityForm


class OpportunityFormResponse(mongo.Document):
    meta = {
        'collection': 'opportunity_form_response',
    }

    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, required=True)
    form = mongo.LazyReferenceField(OpportunityForm, reverse_delete_rule=mongo.NULLIFY)
    form_version = mongo.IntField(required=True)
    data = mongo.DictField(required=True)

    @classmethod
    def create(cls, user: User, form: OpportunityForm, data: dict[str, Any]) -> Self:
        return OpportunityFormResponse(
            user=user,
            form=form,
            form_version=form.version,
            data=data,
        )

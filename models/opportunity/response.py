from typing import (
    Any,
    Self,
)
from datetime import (
    datetime,
    UTC,
)

import mongoengine as mongo

from ..utils import Error
from ..user import User
from .form import (
    OpportunityForm,
    PostValidationErrorCode,
)


class OpportunityFormResponse(mongo.Document):
    meta = {
        'collection': 'opportunity_form_response',
    }

    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, required=True)
    form = mongo.LazyReferenceField(OpportunityForm, reverse_delete_rule=mongo.NULLIFY)
    form_version = mongo.IntField(required=True)
    data = mongo.DictField(required=True)
    creation_time = mongo.DateTimeField(required=True, default=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls, user: User, form: OpportunityForm, data: dict[str, Any]
    ) -> Self | list[Error[PostValidationErrorCode, Any]]:
        errors: list[Error[PostValidationErrorCode, Any]] = []
        for key, input in data.items():
            result = form.fields[key].post_validate_input(key, input, user=user)
            if result is None:
                continue
            errors.extend(result)
        if len(errors) != 0:
            return errors
        return OpportunityFormResponse(
            user=user,
            form=form,
            form_version=form.version,
            data=data,
        ).save()

from enum import IntEnum
import mongoengine as mongo

from ..trans_string.embedded import (
    TransString,
    ContainedTransString,
)
from ..geo import (
    Country,
)
from .opportunity import (
    Opportunity,
)


class FormSubmitMethod(mongo.EmbeddedDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }


class YandexFormsSubmitMethod(FormSubmitMethod):
    URL_REGEX = r'^https://forms.yandex.ru/*$'

    url = mongo.StringField(regex=URL_REGEX, required=True)


class FormField(mongo.EmbeddedDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    label = mongo.EmbeddedDocumentField(TransString, required=True)
    is_required = mongo.BooleanField(required=True)


class StringField(FormField):
    class Fill(IntEnum):
        FIRST_NAME = 0
        SECOND_NAME = 1
        FULLNAME = 2

    max_length = mongo.IntField()
    fill = mongo.EnumField(Fill)


class RegexField(StringField):
    regex = mongo.StringField(required=True)


class TextField(StringField):  # Displayed as HTML text area
    pass


class EmailField(FormField):
    max_length = mongo.IntField()


class PhoneNumberField(FormField):
    whitelist = mongo.ListField(mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY))


class ChoiceField(FormField):
    choices = mongo.MapField(ContainedTransString, required=True)


class FileField(FormField):
    max_size_bytes = mongo.IntField()


class CheckBoxField(FormField):
    checked_by_default = mongo.BooleanField()


class NumberField(FormField):
    class Fill(IntEnum):
        AGE = 0

    min = mongo.IntField()
    max = mongo.IntField()
    fill = mongo.EnumField(Fill)


class DateField(FormField):
    class Fill(IntEnum):
        BIRTHDAY = 0

    fill = mongo.EnumField(Fill)


class OpportunityForm(mongo.Document):
    meta = {
        'collection': 'opportunity_form',
    }

    opportunity = mongo.ReferenceField(
        Opportunity, reverse_delete_rule=mongo.CASCADE, primary_key=True
    )
    version = mongo.IntField(required=True)  # Used for not showing invalid `OpportunityResponse`s
    submit_method = mongo.EmbeddedDocumentField(FormSubmitMethod)
    fields = mongo.MapField(FormField, required=True)

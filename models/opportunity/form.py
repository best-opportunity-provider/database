from typing import (
    Annotated,
    Literal,
    Self,
)
from enum import IntEnum
import re

import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError

from ..pydantic_base import ObjectId
from ..trans_string.embedded import (
    TransString,
    ContainedTransString,
    TransStringModel,
    ContainedTransStringModel,
)
from ..geo import (
    Country,
)
from .opportunity import Opportunity


class FormSubmitMethod(mongo.EmbeddedDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }


class YandexFormsSubmitMethod(FormSubmitMethod):
    URL_REGEX = r'^https://forms\.yandex\.ru/.*$'

    url = mongo.StringField(regex=URL_REGEX, required=True)


class YandexFormsSubmitMethodModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: Literal['yandex_forms']
    url: Annotated[str, pydantic.Field(pattern=YandexFormsSubmitMethod.URL_REGEX)]


type SubmitMethodModels = YandexFormsSubmitMethodModel


class FormField(mongo.EmbeddedDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    label = mongo.EmbeddedDocumentField(TransString, required=True)
    is_required = mongo.BooleanField(required=True)


class FormFieldModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    label: TransStringModel
    is_required: bool


class StringField(FormField):
    class Fill(IntEnum):
        FIRST_NAME = 0
        SECOND_NAME = 1
        FULLNAME = 2

    max_length = mongo.IntField(min_value=1)
    fill = mongo.EnumField(Fill)


class StringFieldModel(FormFieldModel):
    type: Literal['string']
    max_length: Annotated[int, pydantic.Field(ge=1)] | None = None
    fill: StringField.Fill | None = None


class RegexField(StringField):
    regex = mongo.StringField(required=True)


class RegexFieldModel(StringFieldModel):
    type: Literal['regex']
    regex: str

    @pydantic.field_validator('regex', mode='after')
    @classmethod
    def validate_regex(cls, regex: str) -> str:
        try:
            re.compile(regex)
        except re.PatternError:
            raise PydanticCustomError(
                'invalid_pattern',
                'Invalid regex supplied',
            )
        return regex


class TextField(StringField):  # Displayed as HTML text area
    pass


class TextFieldModel(StringFieldModel):
    type: Literal['text']


class EmailField(FormField):
    max_length = mongo.IntField(min_value=1)


class EmailFieldModel(FormFieldModel):
    type: Literal['email']
    max_length: Annotated[int, pydantic.Field(ge=1)] | None = None


class PhoneNumberField(FormField):
    whitelist = mongo.ListField(mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY))


class PhoneNumberFieldModel(FormFieldModel):
    type: Literal['phone_number']
    whitelist: Annotated[list[ObjectId], pydantic.Field(default_factory=list)]


class ChoiceField(FormField):
    choices = mongo.MapField(ContainedTransString, required=True)


class ChoiceFieldModel(FormFieldModel):
    type: Literal['choice']
    choices: Annotated[dict[str, ContainedTransStringModel], pydantic.Field(min_length=1)]


class FileField(FormField):
    max_size_bytes = mongo.IntField(min_value=1)


class FileFieldModel(FormFieldModel):
    type: Literal['file']
    max_size_bytes: Annotated[int, pydantic.Field(ge=1)] | None = None


class CheckBoxField(FormField):
    checked_by_default = mongo.BooleanField()


class CheckBoxFieldModel(FormFieldModel):
    type: Literal['checkbox']
    checked_by_default: bool | None = None


class IntegerField(FormField):
    class Fill(IntEnum):
        AGE = 0

    min = mongo.IntField()
    max = mongo.IntField()
    fill = mongo.EnumField(Fill)


class IntegerFieldModel(FormFieldModel):
    type: Literal['int']
    min: int | None = None
    max: int | None = None
    fill: IntegerField.Fill | None = None

    @pydantic.model_validator
    def validate_bounds(self) -> Self:
        if self.max < self.min:
            raise PydanticCustomError(
                'invalid_bounds',
                'Boundaries must form a non-empty range of values',
            )
        return self


class DateField(FormField):
    class Fill(IntEnum):
        BIRTHDAY = 0

    fill = mongo.EnumField(Fill)


class DateFieldModel(FormFieldModel):
    type: Literal['date']
    fill: DateField.Fill | None = None


type FormFieldModels = (
    StringFieldModel
    | RegexFieldModel
    | TextFieldModel
    | EmailFieldModel
    | PhoneNumberFieldModel
    | ChoiceFieldModel
    | FileFieldModel
    | CheckBoxFieldModel
    | IntegerFieldModel
    | DateFieldModel
)


class OpportunityForm(mongo.Document):
    meta = {
        'collection': 'opportunity_form',
    }

    opportunity = mongo.LazyReferenceField(
        Opportunity, reverse_delete_rule=mongo.CASCADE, primary_key=True
    )
    version = mongo.IntField(required=True)  # Used for not showing outdated `OpportunityResponse`s
    submit_method = mongo.EmbeddedDocumentField(FormSubmitMethod)
    fields = mongo.MapField(FormField, required=True)


class OpportunityFormModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    opportunity: ObjectId
    version: int
    submit_method: Annotated[SubmitMethodModels, pydantic.Field(discriminator='type')] | None = None
    fields: Annotated[
        dict[str, Annotated[FormFieldModels, pydantic.Field(discriminator='type')]],
        pydantic.Field(min_length=1),
    ]

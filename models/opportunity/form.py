from typing import (
    Any,
    Annotated,
    Literal,
    Self,
    Protocol,
    Optional,
)
from enum import IntEnum
import re

import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError

from ..pydantic_base import ObjectId
from ..utils import Error
from ..trans_string.embedded import (
    TransString,
    ContainedTransString,
    TransStringModel,
    ContainedTransStringModel,
    Language,
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

    @classmethod
    def create(cls, model: 'FormSubmitMethodModel') -> Self:
        return model.to_submit_method()


class FormSubmitMethodModel(Protocol):
    def to_submit_method(self) -> FormSubmitMethod: ...


class YandexFormsSubmitMethod(FormSubmitMethod):
    URL_REGEX = r'^https://forms\.yandex\.ru/.*$'

    url = mongo.StringField(regex=URL_REGEX, required=True)


class YandexFormsSubmitMethodModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: Literal['yandex_forms']
    url: Annotated[str, pydantic.Field(pattern=YandexFormsSubmitMethod.URL_REGEX)]

    def to_submit_method(self) -> YandexFormsSubmitMethod:
        return YandexFormsSubmitMethod(url=self.url)


SubmitMethodModels = YandexFormsSubmitMethodModel


class CreateFieldErrorCode(IntEnum):
    PHONE_NUMBER_INVALID_COUNTRY_ID = 0


class FormField(mongo.EmbeddedDocument):
    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    label = mongo.EmbeddedDocumentField(TransString, required=True)
    is_required = mongo.BooleanField(required=True)

    @classmethod
    def create(cls, model: 'FormFieldModel') -> Self | Error[CreateFieldErrorCode, Any]:
        return model.to_field()

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            'label': self.label.get_translation(language),
            'is_required': self.is_required,
        }


class FormFieldModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    label: TransStringModel
    is_required: bool

    def to_field(self, id: str) -> FormField | list[Error[CreateFieldErrorCode, Any]]:
        raise NotImplementedError("This method shouldn't be called")


class StringField(FormField):
    class Fill(IntEnum):
        FIRST_NAME = 0
        SECOND_NAME = 1
        FULLNAME = 2

    max_length = mongo.IntField(min_value=1)
    fill = mongo.EnumField(Fill)

    def to_dict(self, language: Language) -> dict[str, Any]:
        # TODO: make use of fill (via kwargs and some other manipulations)
        return {
            **super().to_dict(language),
            'type': 'string',
            'max_length': self.max_length,
        }


class StringFieldModel(FormFieldModel):
    type: Literal['string']
    max_length: Annotated[int, pydantic.Field(ge=1)] | None = None
    fill: StringField.Fill | None = None

    def to_field(self, _id: str) -> StringField:
        field = StringField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.max_length is not None:
            field.max_length = self.max_length
        if self.fill is not None:
            field.fill = self.fill
        return field


class RegexField(StringField):
    regex = mongo.StringField(required=True)

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'regex',
            'regex': self.regex,
        }


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

    def to_field(self, _id: str) -> RegexField:
        field = RegexField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
            regex=self.regex,
        )
        if self.max_length is not None:
            field.max_length = self.max_length
        if self.fill is not None:
            field.fill = self.fill
        return field


class TextField(FormField):
    max_length = mongo.IntField(min_value=1)

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'text',
            'max_length': self.max_length,
        }


class TextFieldModel(FormFieldModel):
    type: Literal['text']
    max_length: Annotated[int, pydantic.Field(ge=1)] | None = None

    def to_field(self, _id: str) -> TextField:
        field = TextField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.max_length is not None:
            field.max_length = self.max_length
        return field


class EmailField(FormField):
    max_length = mongo.IntField(min_value=1)

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'email',
            'max_length': self.max_length,
        }


class EmailFieldModel(FormFieldModel):
    type: Literal['email']
    max_length: Annotated[int, pydantic.Field(ge=1)] | None = None

    def to_field(self, _id: str) -> EmailField:
        field = EmailField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.max_length is not None:
            field.max_length = self.max_length
        return field


class PhoneNumberField(FormField):
    whitelist = mongo.ListField(mongo.LazyReferenceField(Country))

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'phone_number',
            'whitelist': [str(country.pk) for country in self.whitelist],
        }


class PhoneNumberFieldModel(FormFieldModel):
    type: Literal['phone_number']
    whitelist: Annotated[list[ObjectId], pydantic.Field(min_length=1)] | None = None

    def to_field(
        self, id: str
    ) -> PhoneNumberField | list[Error[CreateFieldErrorCode, tuple[str, int]]]:
        field = PhoneNumberField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.whitelist is None:
            return field
        countries: list[Country] = []
        errors: list[Error[CreateFieldErrorCode, int]] = []
        for index, country_id in enumerate(self.whitelist):
            country: Country | None = Country.objects.with_id(country_id)
            if country is None:
                errors.append(
                    Error[CreateFieldErrorCode, tuple[str, int]](
                        CreateFieldErrorCode.PHONE_NUMBER_INVALID_COUNTRY_ID,
                        (id, index),
                    )
                )
            elif len(errors) == 0:
                countries.append(country)
        if len(errors) != 0:
            return errors
        field.whitelist = countries
        return field


class ChoiceField(FormField):
    choices = mongo.MapField(mongo.EmbeddedDocumentField(ContainedTransString), required=True)

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'choice',
            'choices': {key: label.get_translation(language) for key, label in self.choices},
        }


class ChoiceFieldModel(FormFieldModel):
    type: Literal['choice']
    choices: Annotated[dict[str, ContainedTransStringModel], pydantic.Field(min_length=1)]

    def to_field(self, _id: str) -> ChoiceField:
        return ChoiceField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
            choices={
                key: ContainedTransString.create_from_model(label)
                for key, label in self.choices.items()
            },
        )


class FileField(FormField):
    max_size_bytes = mongo.IntField(min_value=1)

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'file',
            'max_size_bytes': self.max_size_bytes,
        }


class FileFieldModel(FormFieldModel):
    type: Literal['file']
    max_size_bytes: Annotated[int, pydantic.Field(ge=1)] | None = None

    def to_field(self, _id: str) -> FileField:
        field = FileField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.max_size_bytes is not None:
            field.max_size_bytes = self.max_size_bytes
        return field


class CheckBoxField(FormField):
    checked_by_default = mongo.BooleanField()

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **super().to_dict(language),
            'type': 'checkbox',
            'checked': self.checked_by_default or False,
        }


class CheckBoxFieldModel(FormFieldModel):
    type: Literal['checkbox']
    checked_by_default: bool | None = None

    def to_field(self, _id: str) -> CheckBoxField:
        field = CheckBoxField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.checked_by_default is not None and self.checked_by_default:
            field.checked_by_default = True
        return field


class IntegerField(FormField):
    class Fill(IntEnum):
        AGE = 0

    min = mongo.IntField()
    max = mongo.IntField()
    fill = mongo.EnumField(Fill)

    def to_dict(self, language: Language) -> dict[str, Any]:
        # TODO: make use of fill
        return {
            **super().to_dict(language),
            'type': 'integer',
            'min': self.min,
            'max': self.max,
        }


class IntegerFieldModel(FormFieldModel):
    type: Literal['integer']
    min: int | None = None
    max: int | None = None
    fill: IntegerField.Fill | None = None

    @pydantic.model_validator(mode='after')
    def validate_bounds(self) -> Self:
        if self.min is not None and self.max is not None and self.max < self.min:
            raise PydanticCustomError(
                'invalid_bounds',
                'Boundaries must form a non-empty range of values',
            )
        return self

    def to_field(self, _id: str) -> IntegerField:
        field = IntegerField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.min is not None:
            field.min = self.min
        if self.max is not None:
            field.max = self.max
        if self.fill is not None:
            field.fill = self.fill
        return field


class DateField(FormField):
    class Fill(IntEnum):
        BIRTHDAY = 0

    fill = mongo.EnumField(Fill)

    def to_dict(self, language: Language) -> dict[str, Any]:
        # TODO: make use of fill
        return {
            **super().to_dict(language),
            'type': 'date',
        }


class DateFieldModel(FormFieldModel):
    type: Literal['date']
    fill: DateField.Fill | None = None

    def to_field(self, _id: str) -> DateField:
        field = DateField(
            label=TransString.create_from_model(self.label),
            is_required=self.is_required,
        )
        if self.fill is not None:
            field.fill = self.fill
        return field


FormFieldModels = (
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
    version = mongo.IntField(
        required=True,
        default=1,
    )  # Used for not showing outdated `OpportunityResponse`s
    submit_method = mongo.EmbeddedDocumentField(FormSubmitMethod)
    fields = mongo.MapField(mongo.EmbeddedDocumentField(FormField), required=True)

    @classmethod
    def create(
        cls, opportunity: Opportunity, model: 'OpportunityFormModel'
    ) -> Self | list[Error[CreateFieldErrorCode, Any]]:
        self = OpportunityForm(opportunity=opportunity)
        field_errors = self.update_fields(model.fields)
        if field_errors is not None:
            return field_errors
        self.update_submit_method(model.submit_method)
        return self.save()

    def update_submit_method(
        self, submit_method_model: Optional['OpportunityFormModel.SubmitMethodModel']
    ) -> None:
        if submit_method_model is None:
            self.submit_method = None
        else:
            self.submit_method = submit_method_model.to_submit_method()

    def update_fields(
        self, fields_model: 'OpportunityFormModel.FieldsModel'
    ) -> None | list[Error[CreateFieldErrorCode, Any]]:
        errors: list[Error[CreateFieldErrorCode, Any]] = []
        fields: dict[str, FormField] = {}
        for key, field_model in fields_model.items():
            field = field_model.to_field(key)
            if issubclass(type(field), FormField):
                fields[key] = field
                continue
            if isinstance(field, list):
                errors.extend(field)
            else:
                raise 'Unreachable'
        if len(errors) != 0:
            return errors
        self.fields = fields

    def update(
        self, model: 'UpdateOpportunityFormModel'
    ) -> None | list[Error[CreateFieldErrorCode, Any]]:
        if 'fields' in model.model_fields_set:
            errors = self.update_fields(model.fields)
            if errors is not None:
                return errors
        for field in model.model_fields_set:
            match field:
                case 'bump_version':
                    self.version += 1
                case 'submit_method':
                    self.update_submit_method(model.submit_method)
                case _:
                    pass
        self.save()

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {key: field.to_dict(language) for key, field in self.fields.items()}


class OpportunityFormModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type SubmitMethodModel = Annotated[SubmitMethodModels, pydantic.Field(discriminator='type')]
    type FieldsModel = Annotated[
        dict[str, Annotated[FormFieldModels, pydantic.Field(discriminator='type')]],
        pydantic.Field(min_length=1),
    ]

    submit_method: SubmitMethodModel | None = None
    fields: FieldsModel


class UpdateOpportunityFormModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    bump_version: bool = True
    submit_method: OpportunityFormModel.SubmitMethodModel | None = None
    fields: OpportunityFormModel.FieldsModel | None = None

    @pydantic.model_validator(mode='after')
    def validate_model(self) -> Self:
        if len(self.model_fields_set.difference(('bump_version',))) == 0:
            raise PydanticCustomError(
                'empty_update',
                'Update must contain at least 1 field, except `bump_version`',
            )
        if 'fields' in self.model_fields_set and self.fields is None:
            raise PydanticCustomError(
                'null_fields',
                "Form fields can't have an explicit `None` value",
            )
        return self

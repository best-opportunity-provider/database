from typing import Self
from enum import StrEnum
import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError


class Language(StrEnum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'


class TransString(mongo.EmbeddedDocument):
    """String, that provides translations to a subset of supported languages.
    Relies on an external source to store fallback language."""

    meta = {
        'allow_inheritance': True,
    }

    en = mongo.StringField()
    ru = mongo.StringField()

    def get_translation(self, language: Language) -> str | None:
        return getattr(self, language.value, None)

    def has_translation(self, language: Language) -> bool:
        return self.get_translation(language) is not None

    def try_get_translation(self, fallback_language: Language, preferred_language: Language) -> str:
        assert self.has_translation(fallback_language)
        if (preferred := self.get_translation(preferred_language)) is not None:
            return preferred
        return self.get_translation(fallback_language)

    def matches(self, regex: str) -> bool:
        import re

        return any(re.match(regex, field) for field in (self.en, self.ru) if field is not None)

    @classmethod
    def create(cls, text: str, language: Language) -> Self:
        """This method is deprecated. Use `create_from_model` instead."""

        self = TransString()
        setattr(self, language.value, text)
        return self

    @classmethod
    def create_from_model(cls, model: 'TransStringModel') -> Self:
        self = TransString()
        for field in model.model_fields_set:
            setattr(self, field, getattr(model, field))
        return self


class TransStringModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    en: str | None = None
    ru: str | None = None

    @pydantic.model_validator
    def validate_model(self) -> Self:
        if all(translation is None for translation in (self.en, self.ru)):
            raise PydanticCustomError(
                'empty_trans_string',
                'Translation string should contain at least one translation',
            )
        return self


class ContainedTransString(TransString):
    """String, that provides translations to a subset of supported languages
    and stores fallback language."""

    fallback_language = mongo.EnumField(Language, required=True)

    @classmethod
    def create(cls, text: str, language: Language) -> Self:
        self = ContainedTransString(fallback_language=language)
        setattr(self, language.value, text)
        return self

    @classmethod
    def create_from_model(cls, model: 'ContainedTransStringModel') -> Self:
        self = ContainedTransString(fallback_language=model.fallback_language)
        for field in model.model_fields_set:
            setattr(self, field, getattr(model, field))
        return self


class ContainedTransStringModel(TransStringModel):
    fallback_language: Language

    @pydantic.model_validator
    def validate_model(self) -> Self:
        super().validate_model()
        if getattr(self, self.fallback_language) is None:
            raise PydanticCustomError(
                'missing_fallback_translation',
                'Fallback translation is missing',
            )
        return self

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
        self = TransString()
        setattr(self, language.value, text)
        return self


class TransStringModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    en: str
    ru: str


class ContainedTransString(TransString):
    """String, that provides translations to a subset of supported languages
    and stores fallback language."""

    fallback_language = mongo.EnumField(Language, required=True)

    @classmethod
    def create(cls, text: str, language: Language) -> Self:
        self = ContainedTransString(fallback_language=language)
        setattr(self, language.value, text)
        return self


class ContainedTransStringModel(pydantic.BaseModel):
    model_config = {'extra': 'ignore'}
    en: str
    ru: str
    fallback_language: Language

    @pydantic.field_validator('en', 'ru', mode='after')
    def validate_language(self) -> Self:
        if self.fallback_language == Language.ENGLISH:
            if self.en == '':
                raise PydanticCustomError(
                    'fallback_language_error', 'Fallback language should be not empty'
                )
        elif self.fallback_language == Language.RUSSIAN:
            if self.ru == '':
                raise PydanticCustomError(
                    'fallback_language_error', 'Fallback language should be not empty'
                )
        else:
            raise PydanticCustomError(
                'fallback_language_error', 'Fallback language should be a valid language'
            )

from typing import Self
from enum import StrEnum
import mongoengine as mongo


class Language(StrEnum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'


class TransString(mongo.EmbeddedDocument):
    """String, that provides translations to all supported languages."""

    en = mongo.StringField(required=True)
    ru = mongo.StringField(required=True)


class PartialTransString(mongo.EmbeddedDocument):
    """String, that provides translations to a subset of supported languages.
    Relies on an external source to store fallback language."""

    meta = {
        'allow_inheritance': True,
    }

    en = mongo.StringField()
    ru = mongo.StringField()

    def matches(self, regex: str) -> bool:
        import re

        return any(re.match(regex, field) for field in (self.en, self.ru) if field is not None)


class ContainedPartialTransString(PartialTransString):
    """String, that provides translations to a subset of supported languages
    and stores fallback language."""

    fallback_language = mongo.EnumField(Language, required=True)

    @classmethod
    def create(cls, text: str, language: Language) -> Self:
        self = ContainedPartialTransString(fallback_language=language)
        setattr(self, language.value, text)
        return self

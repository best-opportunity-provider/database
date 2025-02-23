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


class ContainedPartialTransString(PartialTransString):
    """String, that provides translations to a subset of supported languages
    and stores fallback language."""

    fallback_language = mongo.EnumField(Language, required=True)

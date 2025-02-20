from typing import Self
from enum import StrEnum
import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError


class Language(StrEnum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'


class TransStringData(mongo.EmbeddedDocument):
    """Auxillary model for `TransString`, containing actual translated strings.

    One benefit of such structure is ability to embed string directly on owner side
    and not in a separate collection.
    """

    fallback_language = mongo.EnumField(Language)
    en = mongo.StringField()
    ru = mongo.StringField()


class TransStringModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra='ignore',
    )

    fallback_language: Language | None = None
    en: str | None = None
    ru: str | None = None

    @pydantic.model_validator(mode='after')
    def check_non_empty(self) -> Self:
        if all(getattr(self, language.value) is None for language in Language):
            raise PydanticCustomError(
                'empty-trans-string',
                'Translation string contains no data',
            )
        return self

    @pydantic.model_validator(mode='after')
    def check_valid_fallback(self) -> Self:
        if (
            self.fallback_language is not None
            and getattr(self, self.fallback_language.value) is None
        ):
            raise PydanticCustomError(
                'missing-fallback-trans',
                'Missing fallback language translation',
                {
                    'fallback': self.fallback_language,
                },
            )
        return self


class TransString(mongo.Document):
    meta = {
        'collection': 'trans_string',
    }

    # We allow arbitrary objects to own trans-strings, so `TransString` knows nothing about its owner.
    # This means, that the strings must be deleted on the owner side and won't be cascaded automatically.
    owner = mongo.GenericLazyReferenceField(required=True)
    data = mongo.EmbeddedDocumentField(TransStringData, required=True)

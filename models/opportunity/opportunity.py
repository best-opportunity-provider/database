from typing import Self
from enum import IntEnum
import mongoengine as mongo

from ..file import File
from ..trans_string import (
    Language,
)
from ..trans_string.embedded import (
    TransString,
    ContainedTransString,
)
from ..geo import (
    Place,
)


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [provider for provider in cls.objects if provider.name.matches(regex)]


class OpportunityIndustry(mongo.Document):
    meta = {
        'collection': 'opportunity_industry',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)


class OpportunityTag(mongo.Document):
    meta = {
        'collection': 'opportunity_tag',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)


class OpportunityLanguage(mongo.Document):
    meta = {
        'collection': 'opportunity_language',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)


class OpportunitySource(mongo.EmbeddedDocument):
    class SourceType(IntEnum):
        PROVIDER_WEBSITE = 0
        AGGREGATOR_WEBSITE = 1
        TELEGRAM = 2

    type = mongo.EnumField(SourceType, required=True)
    link = mongo.StringField(required=True)


class OpportunitySection(mongo.Document):
    meta = {
        'collection': 'opportunity_section',
        'abstract': True,
        'allow_inheritance': True,
    }


class Opportunity(mongo.Document):
    meta = {
        'collection': 'opportunity',
    }

    translations = mongo.ListField(mongo.EnumField(Language), required=True)
    fallback_language = mongo.EnumField(Language, required=True)
    name = mongo.EmbeddedDocumentField(TransString, required=True)
    short_description = mongo.EmbeddedDocumentField(TransString, required=True)
    source = mongo.EmbeddedDocumentField(OpportunitySource, required=True)
    provider = mongo.LazyReferenceField(
        OpportunityProvider,
        reverse_delete_rule=mongo.DENY,
        required=True,
    )
    industry = mongo.LazyReferenceField(
        OpportunityIndustry,
        reverse_delete_rule=mongo.DENY,
        required=True,
    )
    tags = mongo.ListField(mongo.LazyReferenceField(OpportunityTag, reverse_delete_rule=mongo.DENY))
    languages = mongo.ListField(
        mongo.LazyReferenceField(OpportunityLanguage, reverse_delete_rule=mongo.DENY)
    )
    places = mongo.ListField(mongo.LazyReferenceField(Place, reverse_delete_rule=mongo.DENY))
    sections = mongo.ListField(
        mongo.LazyReferenceField(OpportunitySection, reverse_delete_rule=mongo.NULLIFY)
    )

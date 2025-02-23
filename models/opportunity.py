from enum import IntEnum
import mongoengine as mongo

from .file import File
from .trans_string import (
    Language,
)
from .trans_string.embedded import (
    PartialTransString,
    ContainedPartialTransString,
)
from .geo import (
    Country,
    City,
    Place,
)


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    name = mongo.EmbeddedDocumentField(ContainedPartialTransString, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)


class OpportunityFieldOfStudy(mongo.Document):
    meta = {
        'collection': 'opportunity_field_of_study',
    }

    name = mongo.EmbeddedDocumentField(ContainedPartialTransString, required=True)


class OpportunityTag(mongo.Document):
    meta = {
        'collection': 'opportunity_tag',
    }

    name = mongo.EmbeddedDocumentField(ContainedPartialTransString, required=True)


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

    fallback_language = mongo.EnumField(Language, required=True)
    name = mongo.EmbeddedDocumentField(PartialTransString, required=True)
    short_description = mongo.EmbeddedDocumentField(PartialTransString, required=True)
    source = mongo.EmbeddedDocumentField(OpportunitySource, required=True)
    provider = mongo.LazyReferenceField(
        OpportunityProvider,
        reverse_delete_rule=mongo.DENY,
        required=True,
    )
    field_of_study = mongo.LazyReferenceField(
        OpportunityFieldOfStudy,
        reverse_delete_rule=mongo.DENY,
        required=True,
    )
    tags = mongo.ListField(mongo.LazyReferenceField(OpportunityTag, reverse_delete_rule=mongo.DENY))
    places = mongo.ListField(mongo.LazyReferenceField(Place, reverse_delete_rule=mongo.DENY))
    countries = mongo.ListField(mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY))
    cities = mongo.ListField(mongo.LazyReferenceField(City, reverse_delete_rule=mongo.DENY))
    sections = mongo.ListField(
        mongo.LazyReferenceField(OpportunitySection, reverse_delete_rule=mongo.NULLIFY)
    )

from enum import IntEnum
import mongoengine as mongo

from .file import File
from .trans_string import TransStringData
from .geo import Country, City


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    name = mongo.EmbeddedDocumentField(TransStringData, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)


class OpportunityFieldOfStudy(mongo.Document):
    meta = {
        'collection': 'opportunity_field_of_study',
    }

    # Must be provided in all languages, preffered language is not present
    name = mongo.EmbeddedDocumentField(TransStringData, required=True)


class OpportunityTag(mongo.Document):
    meta = {
        'collection': 'opportunity_tag',
    }

    # Must be provided in all languages, preffered language is not present
    name = mongo.EmbeddedDocumentField(TransStringData, required=True)


class OpportunitySource(mongo.EmbeddedDocument):
    class SourceType(IntEnum):
        PROVIDER_WEBSITE = 0
        AGGREGATOR_WEBSITE = 1
        TELEGRAM = 2

    type = mongo.EnumField(SourceType)
    link = mongo.StringField()


class Opportunity(mongo.Document):
    meta = {
        'collection': 'opportunity',
    }

    name = mongo.EmbeddedDocumentField(TransStringData, required=True)
    source = mongo.EmbeddedDocumentField(OpportunitySource, required=True)
    provider = mongo.LazyReferenceField(OpportunityProvider, required=True,
                                        reverse_delete_rule=mongo.DENY)
    field_of_study = mongo.LazyReferenceField(OpportunityFieldOfStudy, reverse_delete_rule=mongo.DENY)
    tags = mongo.ListField(mongo.LazyReferenceField(OpportunityTag, reverse_delete_rule=mongo.DENY))
    countries = mongo.ListField(mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY))
    cities = mongo.ListField(mongo.LazyReferenceField(City, reverse_delete_rule=mongo.DENY))

    ...  # TODO: discuss/add opportunity page content

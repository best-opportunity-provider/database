import mongoengine as mongo

from .trans_string.embedded import (
    TransString,
    ContainedPartialTransString,
)


class Country(mongo.Document):
    meta = {
        'collection': 'country',
    }

    PHONE_CODE_REGEX = r'\+?\d{1,3}'

    name = mongo.EmbeddedDocumentField(TransString, required=True)
    phone_code = mongo.StringField(regex=PHONE_CODE_REGEX, required=True)
    flag_emoji = mongo.StringField(required=True)


class City(mongo.Document):
    meta = {
        'collection': 'city',
    }

    country = mongo.LazyReferenceField(Country, required=True, reverse_delete_rule=mongo.DENY)
    name = mongo.EmbeddedDocumentField(TransString, required=True)


class Place(mongo.Document):
    meta = {
        'collection': 'place',
    }

    name = mongo.EmbeddedDocumentField(ContainedPartialTransString, required=True)
    country = mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY)
    city = mongo.LazyReferenceField(City, reverse_delete_rule=mongo.DENY)

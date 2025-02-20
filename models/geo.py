import mongoengine as mongo

from .trans_string import TransStringData


class Country(mongo.Document):
    meta = {
        'collection': 'country',
    }

    PHONE_CODE_REGEX = r'\d{1,3}'

    # Must be provided in all languages, preffered language is not present
    name = mongo.EmbeddedDocumentField(TransStringData, required=True)
    emoji = mongo.StringField(required=True)
    phone_code = mongo.StringField(regex=PHONE_CODE_REGEX, required=True)


class City(mongo.Document):
    meta = {
        'collection': 'city',
    }

    country = mongo.LazyReferenceField(Country, required=True, reverse_delete_rule=mongo.DENY)
    # Must be provided in all languages, preffered language is not present
    name = mongo.EmbeddedDocumentField(TransStringData, required=True)


class Place(mongo.Document): ...  # TODO: interesting idea to consider (instead of exact addresses)

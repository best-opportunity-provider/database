import mongoengine as mongo

from .user import (
    User,
)


class APIKey(mongo.Document):
    meta = {
        'collection': 'api_key',
        'abstract': True,
        'allow_inheritance': True,
    }

    API_KEY_REGEX = r'^(dev|usr)\-[0-9a-z]{64}$'

    key = mongo.StringField(regex=API_KEY_REGEX, required=True)
    expiry = mongo.DateTimeField(required=True)


class PersonalAPIKey(APIKey):
    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, required=True)
    ip = mongo.StringField(required=True)


class DeveloperAPIKey(APIKey):
    pass

from enum import StrEnum
import mongoengine as mongo


class Language(StrEnum):
    ENGLISH = 'en'
    RUSSIAN = 'ru'


class TransStringData(mongo.EmbeddedDocument):
    """Auxillary model for `TransString`. One benefit of such structure is ability to embed string directly 
       on owner side and not in a separate collection.

       Contains all possible language variants, but none are required.
    """

    fallback_language = mongo.EnumField(Language)
    en = mongo.StringField()
    ru = mongo.StringField()


class TransString(mongo.Document):
    meta = {
        'collection': 'trans_string',
    }

    # We allow arbitrary objects to own trans-strings, so `TransString` knows nothing about its owner.
    # This means, that the strings must be deleted on the owner side and won't be cascaded automatically.
    owner = mongo.GenericLazyReferenceField(required=True)
    data = mongo.EmbeddedDocumentField(TransStringData, required=True)

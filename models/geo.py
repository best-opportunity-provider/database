from typing import (
    Literal,
    Self,
)
import mongoengine as mongo
import pydantic

from .trans_string.embedded import (
    ContainedTransStringModel,
    ContainedTransString,
    Language
)
from .pydantic_base import ObjectId


class Country(mongo.Document):
    meta = {
        'collection': 'country',
    }

    PHONE_CODE_REGEX = r'\+?\d{1,3}'

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    phone_code = mongo.StringField(regex=PHONE_CODE_REGEX, required=True)
    flag_emoji = mongo.StringField(required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.to_dict(language),
            'phone_code': str(self.phone_code),
            'flag_emoji': str(self.flag_emoji)
        }


class City(mongo.Document):
    meta = {
        'collection': 'city',
    }

    country = mongo.LazyReferenceField(Country, required=True, reverse_delete_rule=mongo.DENY)
    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [city for city in cls.objects if city.name.matches(regex)]

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.to_dict(language),
            'country': self.country.to_dict(language)
        }


class Place(mongo.Document):
    meta = {
        'collection': 'place',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    country = mongo.LazyReferenceField(Country, reverse_delete_rule=mongo.DENY, required=True)
    city = mongo.LazyReferenceField(City, reverse_delete_rule=mongo.DENY)

    @classmethod
    def create(
        cls,
        name: ContainedTransStringModel,
        location: 'PlaceLocationModel',
    ) -> Self:
        self = Place()
        self.update(name.to_field(), location.to_field())
        return self

    @classmethod
    def get_all(cls, regex: str = '.*') -> list[Self]:
        return [place for place in cls.objects if place.name.matches(regex)]

    def update(
        self,
        name: ContainedTransString,
        location: Country | City,
    ) -> Self:
        self.name = name
        if isinstance(location, Country):
            self.country = location
        elif isinstance(location, City):
            self.city = location
            self.country = location.fetch().country
        return self.save()

    def to_dict(self, language):
        t = {
            'id': str(self.id),
            'name': self.name.to_dict(language)
        }
        if self.city:
            t['city'] = self.city.to_dict(language)
        else:
            t['country'] = self.country.to_dict(language)
        return t


class PlaceLocationModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: Literal['country', 'city']
    id: ObjectId

    def to_field(self):
        if self.type == 'country':
            return Country.objects.with_id(self.id)
        return City.objects.with_id(self.id)


class PlaceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel
    location: PlaceLocationModel

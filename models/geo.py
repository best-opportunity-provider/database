import re
from typing import Self
import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError

from .trans_string import (
    Language,
)
from .trans_string.embedded import (
    ContainedTransStringModel,
    TransString,
    ContainedTransString,
)


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


class CountryModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }
    name: ContainedTransStringModel
    phone_code: str
    flag_emoji: str

    @pydantic.field_validator('phone_code')
    def validate_regex(self) -> str:
        try:
            re.match(Country.PHONE_CODE_REGEX, self.phone_code)
        except re.PatternError:
            raise PydanticCustomError(
                'pattern_error', 'Phone number should be a valid regular expression'
            )


class City(mongo.Document):
    meta = {
        'collection': 'city',
    }

    country = mongo.LazyReferenceField(Country, required=True, reverse_delete_rule=mongo.DENY)
    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [city for city in cls.objects if city.name.matches(regex)]


class CityModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    country: CountryModel
    name: ContainedTransStringModel


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
        name: str,
        language: Language,
        location: Country | City,
    ) -> Self:
        self = Place(name=ContainedTransString.create(name, language))
        if isinstance(location, Country):
            self.country = location
        elif isinstance(location, City):
            self.city = location
            self.country = location.fetch().country
        return self.save()

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
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


class PlaceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel
    country: CountryModel
    city: CityModel

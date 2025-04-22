from typing import (
    Literal,
    Self,
)
from enum import IntEnum

import mongoengine as mongo
import pydantic
from pydantic_core import PydanticCustomError

from ..pydantic_base import ObjectId
from ..file import File
from ..trans_string import Language
from ..trans_string.embedded import (
    TransString,
    ContainedTransString,
    TransStringModel,
    ContainedTransStringModel
)
from ..geo import Place, PlaceModel


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [provider for provider in cls.objects if provider.name.matches(regex)]

    @classmethod
    def create(cls, name: ContainedTransString) -> Self:
        return OpportunityProvider(name=name).save()


class OpportunityCategory(IntEnum):
    INTERNSHIP = 0
    JOB = 1


class OpportunityIndustry(mongo.Document):
    meta = {
        'collection': 'opportunity_industry',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def create(cls, name: ContainedTransString) -> Self:
        return OpportunityIndustry(name=name).save()

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    def update(self, name: ContainedTransString) -> Self:
        self.name = name
        return self.save()


class OpportunityIndustryModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel


class OpportunityTag(mongo.Document):
    meta = {
        'collection': 'opportunity_tag',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    @classmethod
    def create(cls, name: ContainedTransString) -> Self:
        return OpportunityTag(name=name).save()

    def update(self, name: ContainedTransString) -> Self:
        self.name = name
        return self.save()


class OpportunityTagModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel


class OpportunityLanguage(mongo.Document):
    meta = {
        'collection': 'opportunity_language',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    @classmethod
    def create(cls, name: ContainedTransString) -> Self:
        return OpportunityLanguage(name=name).save()


class OpportunityLanguageModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel


class OpportunitySource(mongo.EmbeddedDocument):
    class Type(IntEnum):
        PROVIDER_WEBSITE = 0
        AGGREGATOR_WEBSITE = 1
        TELEGRAM = 2

    type = mongo.EnumField(Type, required=True)
    link = mongo.StringField(required=True)


class OpportunitySourceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: OpportunitySource.Type
    link: pydantic.HttpUrl  # TODO: validate according to `type`


class OpportunitySection(mongo.Document):
    meta = {
        'collection': 'opportunity_section',
        'abstract': True,
        'allow_inheritance': True,
    }


class MarkdownSection(OpportunitySection):
    title: TransString
    content: TransString

    @classmethod
    def create(cls, title: TransString, content: TransString) -> Self:
        return MarkdownSection(title=title, content=content).save()


class MarkdownSectionModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: Literal['markdown']
    title: TransStringModel
    content: TransStringModel


type OpportunitySectionModels = Annotated[MarkdownSectionModel, Field(discriminator='type')]


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
    category = mongo.EnumField(OpportunityCategory, required=True)
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

    @classmethod
    def create(cls, model: 'CreateModel') -> Self: ...  # TODO

    def update_tags(self, tags: list[OpportunityTag]) -> None: ...  # TODO

    def update_languages(self, languages: list[OpportunityLanguage]) -> None: ...  # TODO

    def update_places(self, places: list[Place]) -> None: ...  # TODO

    def add_section(self, section_model: OpportunitySectionModels) -> None: ...  # TODO

    def delete_section(self, section_id: ObjectId) -> None: ...  # TODO

    def move_section(self, section_id: ObjectId, new_index: int) -> None: ...  # TODO

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [opportunity for opportunity in cls.objects if opportunity.name.matches(regex)]


class CreateModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    fallback_language: Language
    name: TransStringModel
    short_description: TransStringModel
    source: OpportunitySourceModel
    provider: ObjectId
    category: OpportunityCategory
    industry: ObjectId

    @pydantic.model_validator(mode='after')
    def validate_translations(self) -> Self:
        missing_fields: list[str] = []
        for field in ('name', 'short_description'):
            if getattr(getattr(self, field), self.fallback_language.value) is None:
                missing_fields.append(field)
        if len(missing_fields) != 0:
            raise PydanticCustomError(
                'missing_translations',
                'Some fields are missing fallback translations',
                {'fields': missing_fields},
            )
        return self


class UpdateOpportunityModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }
    
    fallback_language: Language
    name: TransStringModel
    short_description: TransStringModel
    source: OpportunitySourceModel
    provider: ObjectId
    category: OpportunityCategory
    industry: ObjectId
    tags: list[OpportunityTagModel]
    languages: list[OpportunityLanguageModel]
    places: list[PlaceModel]
    sections: list[OpportunitySectionModels]

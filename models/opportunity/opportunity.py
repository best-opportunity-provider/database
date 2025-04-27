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
    def create(cls, name: ContainedTransStringModel) -> Self:
        print(type(name))
        return OpportunityIndustry(name=name.to_field()).save()

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    def update(self, name: ContainedTransStringModel) -> Self:
        self.name = name.to_field()
        return self.save()

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.get_translation(language)
        }


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
    def create(cls, name: ContainedTransStringModel) -> Self:
        return OpportunityTag(name=name.to_field()).save()

    def update(self, name: ContainedTransStringModel) -> Self:
        self.name = name.to_field()
        return self.save()

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.get_translation(language)
        }


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
    def create(cls, name: ContainedTransStringModel) -> Self:
        return OpportunityLanguage(name=name.to_field()).save()

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.get_translation(language)
        }


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
    def create(cls, model: 'CreateModel') -> Self:
        obj = Opportunity(
            fallback_language=model.fallback_language,
            name=model.name,
            short_description=model.short_description,
            source=model.source,
            provider=OpportunityProvider.objects.with_id(model.provider),
            category=model.category,
            industry=OpportunityIndustry.objects.with_id(model.industry)
        )
        return obj.save()

    def update_tags(self, tags: list[OpportunityTag]) -> None:
        self.tags = tags

    def update_languages(self, languages: list[OpportunityLanguage]) -> None:
        self.languages = languages

    def update_places(self, places: list[Place]) -> None:
        self.places = places

    def add_section(self, section_model: OpportunitySectionModels) -> None:
        cur = [OpportunitySection(OpportunitySectionModels)]
        for i in self.sections:
            cur.append(i)
        self.sections = cur

    def delete_section(self, section_id: ObjectId) -> None:
        cur = []
        for i in self.sections:
            if i.get('_id') != section_id:
                cur.append(i)
        self.sections = cur

    # def move_section(self, section_id: ObjectId, new_index: int) -> None: ...  # TODO

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

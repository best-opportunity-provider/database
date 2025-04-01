from typing import Self
from enum import IntEnum
import mongoengine as mongo

from formatters import pydantic

from ..file import File, FileModel
from ..trans_string import (
    Language,
)
from ..trans_string.embedded import (
    ContainedTransStringModel,
    TransString,
    ContainedTransString,
    TransStringModel,
)
from ..geo import (
    Place,
    PlaceModel,
)


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [provider for provider in cls.objects if provider.name.matches(regex)]

    def create(cls, name: ContainedTransString):
        self = OpportunityProvider(
            name=name
        )
        return self.save()

class OpportunityProviderModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel
    logo: FileModel
    

class OpportunityIndustry(mongo.Document):
    meta = {
        'collection': 'opportunity_industry',
    }

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)

    @classmethod
    def create(cls, name: ContainedTransString, language: Language) -> Self:
        self = OpportunityIndustry(name=ContainedTransString.create(name, language))
        return self.save()

    @classmethod
    def get_all(cls) -> list[Self]:
        return list(cls.objects)

    def update(
        self,
        name: ContainedTransString
    ) -> Self:
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
        self = OpportunityTag(
            name=name
        )
        return self.save()

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
    
class OpportunityLanguageModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    name: ContainedTransStringModel


class OpportunitySource(mongo.EmbeddedDocument):
    class SourceType(IntEnum):
        PROVIDER_WEBSITE = 0
        AGGREGATOR_WEBSITE = 1
        TELEGRAM = 2

    type = mongo.EnumField(SourceType, required=True)
    link = mongo.StringField(required=True)

class OpportunitySourceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: OpportunitySource.SourceType
    link: str

class OpportunitySection(mongo.Document):
    meta = {
        'collection': 'opportunity_section',
        'abstract': True,
        'allow_inheritance': True,
    }

class OpportunitySectionModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }
    #TODO: ???

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
    def create(
        cls,
        fallback_language: Language,
        name: TransString,
        short_description: TransString,
        source: OpportunitySource,
        provider: OpportunityProvider,
        industry: OpportunityIndustry,
        tags: list[OpportunityTag],
        languages: list[OpportunityLanguage],
        places: list[Place],
        sections: list[OpportunitySection],
    ) -> Self:
        self = Opportunity(
            fallback_language=fallback_language,
            name=name,
            short_description=short_description,
            source=source,
            provider=provider,
            industry=industry,
            tags=tags,
            languages=languages,
            places=places,
            sections=sections,
        )
        return self.save()
    
    def update(
        self,
        fallback_language=fallback_language,
        name=name,
        short_description=short_description,
        source=source,
        provider=provider,
        industry=industry,
        tags=tags,
        languages=languages,
        places=places,
        sections=sections,
    ) -> Self:
        self.fallback_language = fallback_language
        self.name = name
        self.short_description = short_description
        self.source = source
        self.provider = provider
        self.industry = industry
        self.tags = tags
        self.languages = languages
        self.places = places
        self.sections = sections
        return self.save()
    
    def set_logo(self, logo: File) -> Self:
        self.logo = logo
        return self.save()

    @classmethod
    def get_all(cls, regex: str = '*') -> list[Self]:
        return [opportunity for opportunity in cls.objects if opportunity.name.matches(regex)]


class OpportunityModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    translatoions: list[Language]
    fallback_language: Language
    name: TransStringModel
    short_description: TransStringModel
    source: OpportunitySourceModel
    provider: OpportunityProviderModel
    industry: OpportunityIndustryModel
    tags: list[OpportunityTagModel]
    languages: list[OpportunityLanguageModel]
    places: list[PlaceModel]
    sections: list[OpportunitySectionModel]

from typing import (
    Annotated,
    Any,
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
    ContainedTransStringModel,
)
from ..geo import Place


class OpportunityProvider(mongo.Document):
    meta = {
        'collection': 'opportunity_provider',
    }

    DEFAULT_LOGO: str = None

    name = mongo.EmbeddedDocumentField(ContainedTransString, required=True)
    logo = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)

    @classmethod
    def get_all(cls, regex: str = '') -> list[Self]:
        return [provider for provider in cls.objects if provider.name.matches(regex)]

    @classmethod
    def create(cls, name: ContainedTransString) -> Self:
        return OpportunityProvider(name=name).save()

    def to_dict(self, language: Language):
        if self.DEFAULT_LOGO is None:
            self.DEFAULT_LOGO = str(File.objects.get(default_for=File.Bucket.PROVIDER_LOGO).id)
        # NOTE: logo url is not provided here, since it is set on API level
        return {
            'id': str(self.id),
            'name': self.name.get_translation(language),
            'logo': str(self.logo.id) if self.logo is not None else self.DEFAULT_LOGO,
        }


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

    def to_dict(self, language: Language):
        return {'id': str(self.id), 'name': self.name.get_translation(language)}


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

    def to_dict(self, language: Language):
        return {'id': str(self.id), 'name': self.name.get_translation(language)}


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

    def to_dict(self, language: Language):
        return {'id': str(self.id), 'name': self.name.get_translation(language)}


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

    def to_dict(self):
        return {'type': self.type.value, 'link': str(self.link)}


class OpportunitySourceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: OpportunitySource.Type
    link: str  # TODO: validate according to `type`

    def to_document(self) -> OpportunitySource:
        return OpportunitySource(type=self.type, link=self.link)


class OpportunitySection(mongo.Document):
    meta = {
        'collection': 'opportunity_section',
        # 'abstract': True,
        'allow_inheritance': True,
    }


class MarkdownSection(OpportunitySection):
    title = mongo.EmbeddedDocumentField(TransString, required=True)
    content = mongo.EmbeddedDocumentField(TransString, required=True)

    @classmethod
    def create(cls, title: TransStringModel, content: TransStringModel) -> Self:
        instance = MarkdownSection(title=title.to_document(), content=content.to_document())
        return instance.save()

    def to_dict(self, language: Language):
        return {
            'type': 'markdown',
            'title': self.title.get_translation(language),
            'content': self.content.get_translation(language),
        }


class MarkdownSectionModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: Literal['markdown']
    title: TransStringModel
    content: TransStringModel


type OpportunitySectionModels = Annotated[
    MarkdownSectionModel, pydantic.Field(discriminator='type')
]


class Opportunity(mongo.Document):
    meta = {
        'collection': 'opportunity',
        'indexes': [
            {
                'fields': ['is_free'],
                'sparse': True,
            }
        ],
    }

    is_free = mongo.BooleanField()
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

    def section_dict(self, language: Language):
        return [i.fetch().to_dict(language) for i in self.sections]

    def to_dict_min(self, language: Language) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name.try_get_translation(self.fallback_language, language),
            'provider': self.provider.fetch().to_dict(language),
            'category': self.category.value,
        }

    def to_dict(self, language: Language) -> dict[str, Any]:
        return {
            **self.to_dict_min(language),
            'description': self.short_description.try_get_translation(
                self.fallback_language, language
            ),
            'source': self.source.to_dict(),
            'industry': self.industry.fetch().to_dict(language),
            'tags': [
                tag.to_dict(language) for tag in OpportunityTag.objects.filter(id__in=self.tags)
            ],
            'places': [
                place.to_dict(language) for place in Place.objects.filter(id__in=self.places)
            ],
            'languages': [
                lang.to_dict(language)
                for lang in OpportunityLanguage.objects.filter(id__in=self.languages)
            ],
        }

    @classmethod
    def create(
        cls,
        fallback_language: Language,
        name: TransString,
        short_description: TransString,
        source: OpportunitySource,
        provider: OpportunityProvider,
        category: OpportunityCategory,
        industry: OpportunityIndustry,
    ) -> Self:
        self = Opportunity(translations=[fallback_language])
        self.update(
            fallback_language,
            name,
            short_description,
            source,
            provider,
            category,
            industry,
        )
        return self.save()

    def update(
        self,
        fallback_language: Language,
        name: TransString,
        short_description: TransString,
        source: OpportunitySource,
        provider: OpportunityProvider,
        category: OpportunityCategory,
        industry: OpportunityIndustry,
    ) -> None:
        self.fallback_language = fallback_language
        self.name = name
        self.short_description = short_description
        self.source = source
        self.provider = provider
        self.category = category
        self.industry = industry

    def update_tags(self, tags: list[OpportunityTag]) -> None:
        self.tags = tags

    def update_languages(self, languages: list[OpportunityLanguage]) -> None:
        self.languages = languages

    def update_places(self, places: list[Place]) -> None:
        self.places = places

    def add_section(self, section: OpportunitySection) -> None:
        self.sections.append(section)
        self.save()

    def delete_section(self, section: OpportunitySection) -> None:
        new = [sec for sec in self.sections if sec.id != section.id]
        self.sections = new
        section.delete()

    # def move_section(self, section_id: ObjectId, new_index: int) -> None: ...  # TODO

    @classmethod
    def get_all(cls, regex: str = '') -> list[Self]:
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

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

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'name': self.name.get_translation(language)
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

    def to_field(self) -> OpportunityTag:
        return OpportunityTag(name=name.to_field())


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

    def to_dict(self):
        return {
            'type': self.type.value,
            'link': str(self.link)
        }


class OpportunitySourceModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    type: OpportunitySource.Type
    link: str  # TODO: validate according to `type`

    def to_field(self) -> OpportunitySource:
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
        instance = MarkdownSection(title=title.to_field(), content=content.to_field())
        return instance.save()

    def to_dict(self, language: Language):
        return {
            'type': 'markdown',
            'title': self.title.get_translation(language),
            'content': self.content.get_translation(language)
        }


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

    def section_dict(self, language: Language):
        return [i.fetch().to_dict(language) for i in self.sections]

    def to_dict(self, language: Language):
        return {
            'id': str(self.id),
            'translations': [i.value for i in self.translations],
            'fallback_language': self.fallback_language.value,
            'name': self.name.get_translation(language),
            'short_description': self.short_description.get_translation(language),
            'source': self.source.to_dict(),
            'provider': str(self.provider.id),
            'category': self.category.value,
            'industry': str(self.industry.id),
            'tags': [str(i.id) for i in self.tags],
            'languages': [str(i.id) for i in self.languages],
            'places': [str(i.id) for i in self.places],
            'sections': [str(i.id) for i in self.sections]
        }

    @classmethod
    def create(cls, translations, fallback_language, name, short_description, source, provider, category, industry) -> Self:
        obj = Opportunity(
            translations=translations,
            fallback_language=fallback_language,
            name=name,
            short_description=short_description,
            source=source,
            provider=provider,
            category=category,
            industry=industry
        )
        return obj.save()

    # provider: ObjectId
    # industry: ObjectId
    # tags: list[ObjectId]
    # languages: list[ObjectId]
    # places: list[ObjectId]
    # sections: list[ObjectId]

    def update(self, body: 'UpdateOpportunityModel'):
        self.translations = body.translations
        self.fallback_language = body.fallback_language
        self.name = body.name.to_field()
        self.short_description = body.short_description.to_field()
        self.source = body.source.to_field()
        self.provider = OpportunityProvider.objects().with_id(body.provider)
        self.category = body.category
        self.industry = OpportunityIndustry.objects().with_id(body.industry)
        self.tags = [OpportunityTag.objects().with_id(i) for i in body.tags]
        self.languages = [OpportunityLanguage.objects().with_id(i) for i in body.languages]
        self.places = [Place.objects().with_id(i) for i in body.places]
        self.sections = [OpportunitySection.objects().with_id(i) for i in body.sections]
        self.save()

    def update_tags(self, tags: list[OpportunityTag]) -> None:
        self.tags = tags

    def update_languages(self, languages: list[OpportunityLanguage]) -> None:
        self.languages = languages

    def update_places(self, places: list[Place]) -> None:
        self.places = places

    def add_section(self, type: str, section_id: ObjectId) -> None:
        if type == 'markdown':
            self.sections.append(MarkdownSection.objects().with_id(section_id))
        else:
            raise 1
        self.save()

    def delete_section(self, section_id: ObjectId) -> None:
        cur = []
        for i in self.sections:
            if str(i.id) != section_id:
                cur.append(i)
        self.sections = cur

    # def move_section(self, section_id: ObjectId, new_index: int) -> None: ...  # TODO

    @classmethod
    def get_all(cls, regex: str = '') -> list[Self]:
        return [opportunity for opportunity in cls.objects if opportunity.name.matches(regex)]


class CreateModel(pydantic.BaseModel):
    model_config = {
        'extra': 'ignore',
    }

    fallback_language: Language
    translations: list[Language]
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
    
    translations: list[Language]
    fallback_language: Language
    name: TransStringModel
    short_description: TransStringModel
    source: OpportunitySourceModel
    provider: ObjectId
    category: OpportunityCategory
    industry: ObjectId
    tags: list[ObjectId]
    languages: list[ObjectId]
    places: list[ObjectId]
    sections: list[ObjectId]

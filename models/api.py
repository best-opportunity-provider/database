from datetime import (
    datetime,
    UTC,
)
from typing import Self
from ipaddress import IPv4Address
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

    API_KEY_REGEX = r'^(dev|usr)\-[0-9a-f]{64}$'
    PREFIX_TO_TABLE: dict[str, type] = {}  # actual definition at the end of file

    key = mongo.StringField(regex=API_KEY_REGEX, required=True, unique=True)
    expiry = mongo.DateTimeField(required=True)

    @classmethod
    def generate_key(cls, salt: str) -> str:
        from hashlib import sha256

        return sha256(f'{datetime.now()}{salt}'.encode()).hexdigest()[:64]

    @classmethod
    def get(cls, full_key: str) -> Self | None:
        prefix, key = full_key.split('-')
        instance: Self | None = cls.PREFIX_TO_TABLE[prefix].get(key)
        if instance is None:
            return instance
        if instance.expiry <= datetime.now(UTC):
            instance.delete()
            return
        return instance

    def expire(self) -> None:
        self.delete()


class PersonalAPIKey(APIKey):
    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, required=True)
    ip = mongo.StringField(required=True, unique_with='user')

    @classmethod
    def generate(cls, user: User, ip: IPv4Address, expiry: datetime) -> Self:
        if user.id is None:
            # TODO: log message
            raise ValueError("Can't generate personal API key for user without id")
        instance: Self | None = Self.objects.filter(user=user, ip=str(ip)).first()
        if instance is not None:
            instance.delete()
        key = cls.generate_key(f'{user.username}{ip}')
        return PersonalAPIKey(key=key, expiry=expiry, user=user, ip=str(ip)).save()

    @classmethod
    def get(cls, key: str) -> Self | None:
        return PersonalAPIKey.objects.filter(key=key).first()

    def __str__(self):
        return f'usr-{self.key}'


class DeveloperAPIKey(APIKey):
    @classmethod
    def generate(cls, expiry: datetime) -> Self:
        from random import choice

        key = cls.generate_key(''.join([choice('0123456789abcdef') for _ in range(10)]))
        return DeveloperAPIKey(key=key, expiry=expiry).save()

    @classmethod
    def get(cls, key: str) -> Self | None:
        return DeveloperAPIKey.objects.filter(key=key).first()

    def __str__(self):
        return f'dev-{self.key}'


APIKey.PREFIX_TO_TABLE = {
    'usr': PersonalAPIKey,
    'dev': DeveloperAPIKey,
}

from typing import (
    Annotated,
    BinaryIO,
    Self,
    Optional,
)
from datetime import date
from enum import IntEnum
import re

import mongoengine as mongo
from minio import Minio
import pydantic
from pydantic_core import PydanticCustomError

from .file import File
from .utils import Error


USERNAME_REGEX = r'^(?!noreply)[A-Za-z\d]{1,30}$'
EMAIL_REGEX = r'^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[.\-@$!%*?&])[A-Za-z\d.\-@$!%*?&]*$'


class User(mongo.Document):
    meta = {
        'collection': 'user',
    }

    # We do not use `regex` in following fields, because mongoengine doesn't allow
    # skipping validation and pydantic doesn't support look-arounds by default

    username = mongo.StringField(unique=True, required=True)  # `regex=USERNAME_REGEX` ommited
    email = mongo.StringField(required=True)  # `regex=EMAIL_REGEX` ommited
    password_hash = mongo.StringField(max_length=256, required=True)
    avatar = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)

    @classmethod
    def hash_password(cls, password: str) -> str:
        from hashlib import sha256

        return sha256(password.encode()).hexdigest()

    class CreateErrorCode(IntEnum):
        NON_UNIQUE_USERNAME = 0

    class CreateModel(pydantic.BaseModel):
        model_config = {
            'extra': 'ignore',
        }

        # Pydantic doesn't support look-arounds by default, so we check regexes manually

        username: str  # `pattern=USERNAME_REGEX` ommited
        email: str  # `pattern=EMAIL_REGEX` ommited
        password: str  # `pattern=PASSWORD_REGEX` ommited

        @pydantic.field_validator('username', mode='after')
        @classmethod
        def validate_username(cls, username: str) -> str:
            if re.match(USERNAME_REGEX, username) is None:
                raise PydanticCustomError('invalid_pattern', 'Invalid username')
            return username

        @pydantic.field_validator('email', mode='after')
        @classmethod
        def validate_email(cls, email: str) -> str:
            if re.match(EMAIL_REGEX, email) is None:
                raise PydanticCustomError('invalid_pattern', 'Invalid email')
            return email

        @pydantic.field_validator('password', mode='after')
        @classmethod
        def validate_password(cls, password: str) -> str:
            if re.match(PASSWORD_REGEX, password) is None:
                raise PydanticCustomError('invalid_pattern', 'Invalid password')
            return password

    @classmethod
    def create(cls, credentials: CreateModel) -> Self | Error[CreateErrorCode]:
        user: User | None = User.objects.filter(username=credentials.username).first()
        if user is not None:
            return Error(cls.CreateErrorCode.NON_UNIQUE_USERNAME)
        user = User(
            username=credentials.username,
            email=credentials.email,
            password_hash=cls.hash_password(credentials.password),
        ).save()
        UserInfo(user=user).save()
        return user

    class LoginModel(pydantic.BaseModel):
        model_config = {
            'extra': 'ignore',
        }

        username: Annotated[str, pydantic.Field(pattern=USERNAME_REGEX)]
        password: Annotated[str, pydantic.Field(pattern=PASSWORD_REGEX)]

    @classmethod
    def login(cls, credentials: LoginModel) -> Optional['User']:
        user: User | None = User.objects.filter(username=credentials.username).first()
        if user is None or user.password_hash != cls.hash_password(credentials.password):
            return
        return user

    def update_avatar(self, minio_client: Minio, file: BinaryIO, extension: str) -> None:
        avatar = File.create(
            minio_client,
            file,
            extension,
            File.Bucket.USER_AVATAR,
            access_mode=File.AccessMode.PUBLIC,
        )
        if isinstance(avatar, File.CreateError):
            raise
        self.avatar = avatar
        self.save()

    def get_avatar(self, minio_client: Minio) -> bytes:
        filename: str = self.avatar.fetch().name if self.avatar is not None else 'default.png'
        # TODO: perhaps this logic belongs to `File` (add classmethod)
        response = None
        try:
            response = minio_client.get_object('user-avatar', filename)
            avatar = response.read()
        finally:
            if response is not None:
                response.close()
                response.release_conn()
        return avatar


class UserInfo(mongo.Document):
    meta = {
        'collection': 'user_info',
    }

    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, primary_key=True)
    name = mongo.StringField()
    surname = mongo.StringField()
    birthday = mongo.DateField()

    class UpdateModel(pydantic.BaseModel):
        model_config = {
            'extra': 'ignore',
        }

        name: str | None = None
        surname: str | None = None
        birthday: date | None = None

    def _update_name(self, name: str) -> None:
        self.name = name

    def _update_surname(self, surname: str) -> None:
        self.surname = surname

    def _update_birthday(self, birthday: date) -> None:
        self.birthday = date

    _update_field_handlers = {
        'name': _update_name,
        'surname': _update_surname,
        'birthday': _update_birthday,
    }

    def update(self, fields: UpdateModel) -> None:
        for field in fields.model_fields_set:
            self._update_field_handlers[field](self, getattr(fields, field))

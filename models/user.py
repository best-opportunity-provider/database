from typing import Annotated
import mongoengine as mongo
import pydantic

from .file import File


class User(mongo.Document):
    meta = {
        'collection': 'user',
    }

    USERNAME_REGEX = r'^(?!noreply)[A-Za-z\d]{1,30}$'
    EMAIL_REGEX = r'^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$'
    PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[.\-@$!%*?&])[A-Za-z\d.\-@$!%*?&]*$'

    username = mongo.StringField(regex=USERNAME_REGEX, unique=True, required=True)
    email = mongo.StringField(regex=EMAIL_REGEX, required=True)
    password_hash = mongo.StringField(max_length=256, required=True)
    avatar = mongo.LazyReferenceField(File, reverse_delete_rule=mongo.NULLIFY)


class UserInfo(mongo.Document):
    meta = {
        'collection': 'user_info',
    }

    user = mongo.LazyReferenceField(User, reverse_delete_rule=mongo.CASCADE, primary_key=True)
    name = mongo.StringField()
    surname = mongo.StringField()
    birthday = mongo.DateField()


class LoginCredentialsModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra='ignore',
    )

    username: Annotated[str, pydantic.Field(pattern=User.USERNAME_REGEX)]
    password: Annotated[str, pydantic.Field(pattern=User.PASSWORD_REGEX)]


class RegistrationCredentialsModel(LoginCredentialsModel):
    email: Annotated[str, pydantic.Field(pattern=User.EMAIL_REGEX)]

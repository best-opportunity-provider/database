import mongoengine as mongo


class User(mongo.Document):
    meta = {
        'collection': 'user',
    }

    USERNAME_REGEX = r'^(?!noreply)[A-Za-z\d]{1,30}$'

    username = mongo.StringField(regex=USERNAME_REGEX, required=True)
    password = mongo.StringField(max_length=256, required=True)
    avatar = mongo.LazyReferenceField('File')
    info = mongo.LazyReferenceField('UserInfo', required=True,
                                    reverse_delete_rule=mongo.CASCADE)


class UserInfo(mongo.Document):
    meta = {
        'collection': 'user_info',
    }

    user = mongo.LazyReferenceField('User', reverse_delete_rule=mongo.CASCADE)

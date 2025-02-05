from typing import Self
from enum import IntEnum
import mongoengine as mongo


class File(mongo.Document):
    meta = {
        'collection': 'file',
    }

    FILE_EXTENSION_REGEX = r'^[A-Za-z]+(.[A-Za-z]+)*$'

    class AccessMode(IntEnum):
        PRIVATE = 0
        PUBLIC = 1

    extension = mongo.StringField(regex=FILE_EXTENSION_REGEX, required=True)
    access_mode = mongo.EnumField(AccessMode, required=True)
    # We allow arbitrary objects to own files, so `File` knows nothing about its owner.
    # This means, that the files must be deleted on the owner side and won't be cascaded automatically.
    owner = mongo.GenericLazyReferenceField()

    @classmethod
    def create(cls) -> Self:
        ...

    def delete(self) -> None:
        ...  # TODO: delete file instance in MinIO

    def can_access(self, accessor_id: mongo.fields.ObjectId) -> bool:
        match self.access_mode:
            case File.AccessMode.PUBLIC:
                return True
            case File.AccessMode.PRIVATE:
                return self.owner_id == accessor_id
        raise NotImplementedError('Unhandled `File.AccessMode`')

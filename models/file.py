from typing import BinaryIO, Self
from enum import IntEnum
import re
import mongoengine as mongo
import minio


class File(mongo.Document):
    meta = {
        'collection': 'file',
    }

    FILE_EXTENSION_REGEX = r'^[A-Za-z]+(.[A-Za-z]+)*$'

    class AccessMode(IntEnum):
        PRIVATE = 0
        PUBLIC = 1

    class State(IntEnum):
        ALIVE = 0
        MARKED_FOR_DELETION = 1

    extension = mongo.StringField(regex=FILE_EXTENSION_REGEX, required=True)
    # We allow arbitrary objects to own files, so `File` knows nothing about its owner.
    # This means, that the files must be deleted on the owner side and won't be cascaded automatically.
    owner = mongo.GenericLazyReferenceField()
    access_mode = mongo.EnumField(AccessMode, required=True)
    state = mongo.EnumField(State, required=True)
    bucket = mongo.StringField()  # If not specified, 'file' is used

    @classmethod
    def get_name(cls, object_id: mongo.fields.ObjectId, extension: str) -> str:
        return f'{object_id}.{extension}'

    @property
    def name(self) -> str:
        return self.get_name(self.pk, self.extension)

    class CreateError(IntEnum):
        INVALID_EXTENSION = 0
        S3_UPLOAD_ERROR = 1

    @classmethod
    def create(
        cls,
        minio_client: minio.Minio,
        file: BinaryIO,
        size: int,
        extension: str,
        access_mode: AccessMode = AccessMode.PRIVATE,
        owner: mongo.fields.ObjectId | None = None,
        bucket: str = 'file',
    ) -> Self | CreateError:
        if not re.match(cls.FILE_EXTENSION_REGEX, extension):
            return cls.CreateError.INVALID_EXTENSION
        instance = File(
            extension=extension, access_mode=access_mode, state=cls.State.ALIVE, bucket=bucket
        )
        if owner is not None:
            instance.owner = owner
        instance: File = instance.save()
        try:
            minio_client.put_object(bucket, cls.get_name(instance.pk, extension), file, size)
        except minio.S3Error:
            instance.delete()
            return cls.CreateError.S3_UPLOAD_ERROR
        return instance

    def mark_for_deletion(self) -> None:
        """Marks file for deletion. After call file is considered to be deleted.

        Actual call alters only MongoDB state and is not instantly observable from S3 perspective,
        because actual deletion is handled by separate worker.
        """

        self.state = self.State.MARKED_FOR_DELETION
        self.save()

    class DeleteError(IntEnum): ...

    def handle_deletion(
        self, minio_client: minio.Minio, bucket: str = 'file'
    ) -> None | DeleteError:
        # TODO: this needs documentation
        # Thing must rely on bucket versioning, although I don't know details yet
        ...

    def can_access(self, accessor_id: mongo.fields.ObjectId) -> bool:
        if self.state != self.State.ALIVE:
            return False
        match self.access_mode:
            case File.AccessMode.PUBLIC:
                return True
            case File.AccessMode.PRIVATE:
                return self.owner_id == accessor_id
        raise NotImplementedError('Unhandled `File.AccessMode`')

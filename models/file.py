from typing import BinaryIO, Self
from enum import IntEnum
import re
import mongoengine as mongo
import minio
import pydantic


class File(mongo.Document):
    meta = {
        'collection': 'file',
    }

    class AccessMode(IntEnum):
        PRIVATE = 0
        PUBLIC = 1

    class State(IntEnum):
        ALIVE = 0
        MARKED_FOR_DELETION = 1

    class Bucket(IntEnum):
        USER_AVATAR = 0
        PROVIDER_LOGO = 1

    FILE_EXTENSION_REGEX = r'^[A-Za-z]+(.[A-Za-z]+)*$'
    BUCKET_NAMES = {
        Bucket.USER_AVATAR: 'user_avatar',
        Bucket.PROVIDER_LOGO: 'opportunity_provider_logo',
    }

    extension = mongo.StringField(regex=FILE_EXTENSION_REGEX, required=True)
    access_mode = mongo.EnumField(AccessMode, required=True)
    state = mongo.EnumField(State, required=True)
    bucket = mongo.EnumField(Bucket, required=True)

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
        extension: str,
        bucket: Bucket,
        size: int | None = None,
        access_mode: AccessMode = AccessMode.PRIVATE,
    ) -> Self | CreateError:
        if not re.match(cls.FILE_EXTENSION_REGEX, extension):
            return cls.CreateError.INVALID_EXTENSION
        instance: File = File(
            extension=extension,
            access_mode=access_mode,
            state=cls.State.ALIVE,
            bucket=bucket,
        ).save()
        try:
            minio_client.put_object(
                bucket,
                cls.get_name(instance.pk, extension),
                file,
                size if size is not None else -1,
                part_size=5_242_880,
            )
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
        self,
        minio_client: minio.Minio,
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

class FileModel(pydantic.BaseModel):
    extension: str
    access_mode: File.AccessMode
    state: File.State
    bucket: File.Bucket

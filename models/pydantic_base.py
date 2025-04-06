from typing import Annotated

import pydantic


OBJECT_ID_REGEX = r'^(\d[abcdef]){24}$'
type ObjectId = Annotated[str, pydantic.Field(pattern=OBJECT_ID_REGEX)]

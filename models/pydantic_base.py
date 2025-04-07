from typing import Annotated

import pydantic


OBJECT_ID_REGEX = r'^([\dabcdef]){24}$'
type ObjectId = Annotated[str, pydantic.Field(pattern=OBJECT_ID_REGEX)]

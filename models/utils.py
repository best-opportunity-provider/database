from enum import Enum


class Error[Code: Enum, Context = None]:
    error_code: Code
    context: Context

    def __init__(self, error_code: Code, context: Context = None) -> None:
        self.error_code = error_code
        self.context = context

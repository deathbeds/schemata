class ConsentException(BaseException):
    pass


class ValidationError(BaseException):
    pass


ValidationErrors = (
    ValidationError,
    __import__("jsonschema").ValidationError,
    ValueError,
    ConsentException,
)

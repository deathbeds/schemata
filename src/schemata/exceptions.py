import inspect
from contextlib import suppress

from . import utils

globals().update(
    {x: getattr(utils.testing, x) for x in dir(utils.testing) if x.startswith("assert")}
)
__all__ = ("ValidationError",)


class ConsentException(BaseException):
    pass


def raises(*args):
    assertRaises(BaseException, partial(*args))


class ValidationException(BaseException):
    """an exception handling context that can extract schema and object paths to exceptions"""

    def __init__(self, type=None, schema=None, path=None, items=1, parent=None):
        if isinstance(type, dict):
            from . import builders

            type = builders.InstanceBuilder(type).build()
        self.type = type
        self.schema = schema
        self.path = path
        self.exceptions = []
        self.items = items
        if not parent:
            self.parent = self.root = self
        else:
            self.parent = parent
            self.root = parent.root

    def __enter__(self):
        return self

    def __exit__(self, type, exception, traceback):
        if not (type is exception is traceback is None):
            if exception not in self.exceptions:
                self.exceptions.append(exception)
                if len(self.exceptions) >= self.items:
                    if self is self.root:
                        self.__cause__ = None
                    raise self

        return True

    def push(self, *, type=None, schema=None, path=None, items=1):
        return ValidationException(
            type=type, schema=schema, parent=self, path=path, items=items
        )

    def get_validators(self, *checked):
        for t in reversed(inspect.getmro(self.type)):
            if utils.is_validator(t):
                if t.validator.__func__ not in checked:
                    yield t
                    checked += (t.validator.__func__,)

    def validate(self, object):
        from . import types

        for validator in self.get_validators():
            with self:
                with self.push(schema=validator.key()) as exception:
                    validator.validator.__func__(self.type, object)

        return self

    def raises(self):
        if self.exceptions:
            raise self
        return self

    def ravel(self):
        for exception in ravel_exceptions(self.exceptions):
            yield from map(ravel_paths, list(ravel_exception(exception, self)))

    def report(self):
        shift = [0, 0]
        exceptions = list(self.ravel())
        for schema, path, exception in exceptions:
            shift = [max(shift[0], len(schema)), max(shift[1], len(path))]

        return "\n".join(
            "❗"
            + x
            + " " * (shift[0] - len(x))
            + " @"
            + y
            + " " * (shift[1] - len(y))
            + ": "
            + str(z)
            for x, y, z in exceptions
        )

    def __str__(self):
        return "\n" + self.report()

    __repr__ = report


def ravel_exceptions(object):
    if isinstance(object, list):
        for object in object:
            yield from ravel_exceptions(object)
    else:

        yield object


def ravel_exception(e, *ordered):
    ordered = ordered or (e,)
    if e not in ordered:
        ordered += (e,)
    if isinstance(e, ValidationException):
        for exception in e.exceptions:
            if exception not in ordered:
                yield from map(ravel_paths, ravel_exception(exception, *ordered))
    else:
        yield ordered


def ravel_paths(exceptions):
    import jsonpointer

    schema, path = (), ()
    final = None
    for exception in exceptions:
        if isinstance(exception, ValidationException):
            if exception.schema is not None:
                schema += (exception.schema,)
            if exception.path is not None:
                path += (exception.path,)
        else:
            final = exception
            break
    return (
        jsonpointer.JsonPointer.from_parts(schema).path,
        jsonpointer.JsonPointer.from_parts(path).path or "/",
        final,
    )


def ravel_exception(exception, *ordered):
    if exception not in ordered:
        ordered += (exception,)
    if isinstance(exception, ValidationException):
        for exception in exception.exceptions:
            yield from ravel_exception(exception, *ordered)
    else:
        yield ordered

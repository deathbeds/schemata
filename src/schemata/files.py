from . import mediatypes, strings, utils
from .types import EMPTY, Default, Examples, Type


class Dir(Type, utils.Path):
    def __class_getitem__(cls, object):
        return cls + Default[object]

    @classmethod
    def py(cls):
        return utils.Path


class File(Dir):
    def load(self, cls=EMPTY):
        with self.open("r") as file:
            if hasattr(self, "loads"):
                object = self.loads(file.read())
            else:
                object = file.read()
        if cls is EMPTY:
            return object
        return cls(object)

    def dump(self, object):
        with self.open("w") as file:
            if hasattr(self, "dumps"):
                file.write(self.dumps(object))
            mt = type(self).value(mediatypes.ContentMediaType)
            if mt is EMPTY:
                return strings.String
            return strings.String + mt

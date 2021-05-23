from .types import EMPTY, ContentMediaType, Default, Examples, Type
from .utils import Path


class Dir(Type, Path):
    def __class_getitem__(cls, object):
        return cls + Default[object]

    @classmethod
    def py(cls):
        return Path


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
            mt = type(self).value(ContentMediaType)
            if mt is EMPTY:
                return String
            return String + mt

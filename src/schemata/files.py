from . import formats, mediatypes, strings, utils
from .types import EMPTY, Default, Examples, Type


class Dir(Type, formats.Format["file-format"], utils.Path):
    def __new__(cls, *object, **kw):
        return utils.Path.__new__(cls, *object, **kw)

    def __class_getitem__(cls, object):
        return cls + Default[object]

    @classmethod
    def py(cls):
        return utils.Path


class File(Dir):
    def mediatype(self):
        return mediatypes.mimetypes.guess_type(str(self))[0]

    def load(self, cls=EMPTY):
        if hasattr(self, "loads"):
            loader = self.loads
        else:
            loader = mediatypes.ContentMediaType.get_loader(self.mediatype()).loads
        object = loader(self.read_text())

        if cls is EMPTY:
            return object
        return cls(object)

    def dump(self, object):
        if hasattr(self, "dumps"):
            dumper = self.dumps
        else:
            dumper = mediatypes.ContentMediaType.get_dumper(self.mediatype()).dumps
        object = loader(self.read_text())

        if cls is EMPTY:
            return object
        return cls(object)

from . import formats, mediatypes, strings, utils
from .types import EMPTY, Any, Type


class Dir(Any, utils.Path):
    def __new__(cls, *object, **kw):
        return utils.Path.__new__(cls, *object, **kw)

    def __class_getitem__(cls, object):
        return cls + Any.Default[object]

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
            try:
                loader = mediatypes.ContentMediaType.get_loader(self.mediatype()).loads
            except AssertionError:
                loader = mediatypes.FileExtension.get_loader(self.suffix).loads
        object = loader(self.read_text())

        if isinstance(object, str):
            return (strings.String + mediatypes.ContentMediaType[self.mediatype()])(
                object
            )
        if cls is EMPTY:
            return object
        return cls(object)

    def dump(self, object):
        if hasattr(self, "dumps"):
            dumper = self.dumps
        else:
            try:
                dumper = mediatypes.ContentMediaType.get_dumper(self.mediatype()).dumps
            except AssertionError:
                dumper = mediatypes.FileExtension.get_dumper(self.suffix).dumps

        return self.write_text(dumper(object))

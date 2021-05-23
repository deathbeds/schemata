from . import Type


class Patch(Type):
    def __class_getitem__(cls, object):
        pass

    class Op(Type):
        pass

    class Path(Type):
        pass

    class From(Path):
        pass


class Add(Patch.Op["add"]):
    pass


class Remove(Patch.Op["remove"]):
    pass


class Replace(Patch.Op["remove"]):
    pass


class Copy(Patch.Op["copy"]):
    pass


class Move(Patch.Op["move"]):
    pass


class Test(Patch.Op["test"]):
    pass

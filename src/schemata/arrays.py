from .types import List, Patch


class IList(Patch, List):
    """a mutable list with validation"""

    # list has a copy method, i'm not sure what schemata should do with it.
    copy, clear, count, sort, reverse, index = (
        list.copy,
        list.clear,
        list.count,
        list.sort,
        list.reverse,
        list.index,
    )

    def append(self, object):
        self.extend((object,))

    def extend(self, args=None):
        if self._push_mode:
            return list.extend(self, args)
        with self:
            for x in args or []:
                self.add(-1, x)

    def insert(self, id, value):
        if self._push_mode:
            return list.insert(self, id, value)
        with self:
            self.add(id, value)

    def pop(self, index=-1):
        with self:
            if index == -1:
                index = len(self) - 1
            return super().remove(index)

    def remove(self, value):
        self.pop(self.index(value))

    __getitem__ = list.__getitem__

    def __setitem__(self, key, value):
        if self._push_mode:
            return list.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    __iadd__ = extend

    def __add__(self, object):
        return type(self)(list.__add__(self, object))

    def __delitem__(self, x):
        return list.__delitem__(self, x)

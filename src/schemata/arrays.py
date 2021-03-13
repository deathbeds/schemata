from .types import List, Patch


class IList(Patch, List):
    """a mutable list with validation"""

    def copy(self, source=None, target=None):
        if self._push_mode:
            return dict.copy(self)
        with self:
            return self.copy(source, target)

    def append(self, *args):
        if self._push_mode:
            return list.append(self, *args)
        self.extend((args,))

    def extend(self, args=None):
        if self._push_mode:
            return list.extend(self, *args)
        with self:
            self.patches(*(dict(path="/-", value=x, **self.ADD) for x in args or []))

    def insert(self, id, value):
        if self._push_mode:
            return list.insert(self, id, value)
        with self:
            self.add(id, value)

    def pop(self, key, default=None):
        if self._push_mode:
            return list.pop(self, key, default)
        with self:
            return self.remove(key)

    def remove(self, value):
        if self._push_mode:
            return list.remove(self, value)
        with self:
            super().remove(self.index(value))

    def __getitem__(self, key):
        if self._push_mode:
            return list.__getitem__(self, key)
        return self.resolve(key)

    def __setitem__(self, key, value):
        if self._push_mode:
            return list.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    __add__ = extend

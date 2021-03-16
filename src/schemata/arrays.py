from .types import List, Patch


class IList(Patch, List):
    """a mutable list with validation"""

    def copy(self, source=None, target=None):
        if self._push_mode:
            return dict.copy(self)
        with self:
            return self.copy(source, target)

    def append(self, object):
        self.extend((object,))

    add = append

    def extend(self, args=None):
        if self._push_mode:
            return list.extend(self, args)
        with self:
            self.add_patches(
                *(dict(path="/-", value=x, **self.ADD) for x in args or [])
            )

    def insert(self, id, value):
        if self._push_mode:
            return list.insert(self, id, value)
        with self:
            self.add(id, value)

    def pop(self, index=-1):
        if self._push_mode:
            return list.pop(self, index)
        with self:
            return super().remove(str(len(self) - 1 if index == -1 else index))

    def remove(self, value):
        if self._push_mode:
            return list.remove(self, value)
        self.pop(self.index(value))

    def __getitem__(self, key):
        if isinstance(key, str):
            if self._push_mode:
                return list.__getitem__(self, key)
            return self.resolve(key)
        return list.__getitem__(self, key)

    def __setitem__(self, key, value):
        if self._push_mode:
            return list.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    def replace(self, key, value):
        # replace patch
        with self:
            super().replace(key, value)

    def move(self, key, target):
        with self:
            super().move(key, target)

    __iadd__ = __add__ = extend

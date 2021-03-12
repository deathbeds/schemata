from . import literal as L, base as B


class Patch:
    """the patch class implements the json patch protocol, for lazy updating and validation to lists and dictionaries"""

    ADD = dict(op="add")
    REMOVE = dict(op="remove")
    REPLACE = dict(op="replace")
    COPY = dict(op="copy")
    MOVE = dict(op="move")
    TEST = dict(op="test")

    _depth = 0
    _push = 0

    @staticmethod
    def pointer(x):
        import jsonpointer

        if isinstance(x, str):
            if x.startswith("/"):
                return jsonpointer.JsonPointer(x).path
            x = (x,)
        if isinstance(x, tuple):
            return jsonpointer.JsonPointer.from_parts(x).path
        raise BaseException("dunno")

    def __enter__(self):
        self._depth += 1
        return self

    def __exit__(self, *e):
        self._depth -= 1
        if not self._depth:
            # a depth indicates we should collect our patches, verify and apply them.
            self.verify()

    def verify(self):
        with self.push():
            x = self.inc()

        try:
            self.validate(x)
        except B.ValidationErrors as e:
            self.reset()
            raise e

        with self.push():
            self.apply()

    def push(self):
        """enter a push mode state where the dictionary can apply standard changes,
        otherwise we only record the patches"""
        import contextlib

        @contextlib.contextmanager
        def push_mode():
            self._push += 1
            yield self
            self._push -= 1

        return push_mode()

    def apply(self):
        """apply the stored json patches to the object"""
        import jsonpatch

        with self.push():
            jsonpatch.apply_patch(self, self._patches, in_place=True)
            self.reset()
        return self

    def inc(self):
        """created a temporary instance of the patched object"""
        import jsonpatch

        if not hasattr(self, "_tmp"):
            self._patches, self._applied_patches = [], []
            t = type(self)
            if issubclass(t, list):
                self._tmp = list(self)
            if issubclass(t, dict):
                self._tmp = dict(self)

        with self.push():
            self._tmp = jsonpatch.apply_patch(self._tmp, self._patches, in_place=False)
            while self._patches:
                self._applied_patches += self._patches.pop(0)

        return self._tmp

    def resolve(self, x):
        import jsonpointer

        with self.push():
            self = jsonpointer.resolve_pointer(self, Patch.pointer(x))
        return self

    def patch(self, *patch):
        if not hasattr(self, "_patches"):
            self._patches, self._applied_patches = [], []

        for p in patch:
            if "from" in p:
                p["from"] = Patch.pointer(p["from"])
            p["path"] = Patch.pointer(p["path"])
            self._patches.append(p)

        return self

    def add(self, key, value):
        return self.patch(dict(path=key, value=self[key], **self.ADD))

    def remove(self, key, *default):
        return self.patch(dict(path=key, value=self[key], **self.REMOVE))

    def move(self, key, target):
        return self.patch(dict(path=target, **{"from": key}, **self.MOVE))

    def copy(self, key, target):
        return self.patch(dict(path=target, **{"from": key}, **self.COPY))

    def replace(self, key, value):
        return self.patch(dict(path=key, value=value, **self.REPLACE))

    def reset(self):
        self._depth = self._push = 0
        for x in (self._patches, self._applied_patches, self._tmp):
            while x:
                if isinstance(x, list):
                    x.pop()
                elif isinstance(x, dict):
                    x.popitem()


class IList(Patch, L.List):
    """a mutable list with validation"""

    def copy(self, source=None, target=None):
        if self._push:
            return dict.copy(self)
        with self:
            return self.copy(source, target)

    def append(self, *args):
        if self._push:
            return list.append(self, *args)
        self.extend((args,))

    def extend(self, args=None):
        if self._push:
            return list.extend(self, *args)
        with self:
            self.patch(*(dict(path="/-", value=x, **self.ADD) for x in args or []))

    def insert(self, id, value):
        if self._push:
            return list.insert(self, id, value)
        with self:
            self.add(id, value)

    def pop(self, key, default=None):
        if self._push:
            return list.pop(self, key, default)
        with self:
            return self.remove(key)

    def remove(self, value):
        if self._push:
            return list.remove(self, value)
        with self:
            super().remove(self.index(value))

    def __getitem__(self, key):
        if self._push:
            return list.__getitem__(self, key)
        return self.resolve(key)

    def __setitem__(self, key, value):
        if self._push:
            return list.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    __add__ = extend


class IDict(Patch, L.Dict):
    """a mutable dict with validation"""

    def copy(self, source=None, target=None):
        if self._push:
            return dict.copy(self)
        with self:
            return self.copy(source, target)

    def get(self, key, default=None):
        return self.resolve(key)

    def pop(self, key, default=None):
        if self._push:
            return dict.pop(self, key, default)
        with self:
            return self.remove(key)

    def __getitem__(self, key):
        if self._push:
            return dict.__getitem__(self, key)
        with self.push():
            return self.resolve(key)

    def __setitem__(self, key, value):
        if self._push:
            return dict.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    def update(self, *args, **kwargs):
        if not hasattr(self, "_patches"):
            dict.update(self, dict(*args, **kwargs))
            self._patches = []
            return self

        with self:
            for k, v in dict(*args, **kwargs).items():
                self.replace(k, v)

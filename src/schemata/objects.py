from .types import Dict, Patch


class IDict(Patch, Dict):
    """a mutable dict with validation"""

    copy = dict.copy

    def pop(self, key, default=None):
        with self:
            return self.remove(key)

    def __getitem__(self, key):
        if self._push_mode:
            return dict.__getitem__(self, key)
        with self.push_mode():
            return self.resolve(key)

    def __setitem__(self, key, value):
        if self._push_mode:
            return dict.__setitem__(self, key, value)
        with self:
            self.replace(key, value)

    def update(self, *args, **kwargs):
        if not hasattr(self, "_patches"):
            dict.update(self, dict(*args, **kwargs))
            self._patches, self._applied_patches, self._tmp = [], [], dict(self)
            return self

        with self:
            for k, v in dict(*args, **kwargs).items():
                if k in self:
                    self.replace(k, v)
                else:
                    self.add(k, v)

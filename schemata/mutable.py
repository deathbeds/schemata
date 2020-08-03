"""Constraints for mutable objects."""
import collections
import typing

_ = __import__("gettext").gettext


class display:
    def _ipython_display_(self):
        import IPython
        data, meta = super()._repr_mimebundle_()
        if not hasattr(self, "_display_id"):
            
            self._display_id = IPython.display.display(
                data, metadata=meta, display_id=True, raw=True
            )
        else:
            self._display_id.display(
                data, metadata=meta, raw=True
            )

    def _propagate(self):
        if hasattr(self, '_display_id'):
            data, meta = super()._repr_mimebundle_()
            self._display_id.update(data, metadata=meta, raw=True)


class mapping:
    def __setitem__(self, name, value):
        self.validate({**self, name: value})
        super().__setitem__(name, value)
        self._propagate()

    def update(self, arg=None, **kwargs):
        test = {**self}
        if arg:
            test.update(arg)
        test.update(kwargs)
        self.validate(test)
        super().update(arg or {}, **kwargs)
        self._propagate()

    def __delitem__(self, key):
        self.validate({k: v for k, v in self.items() if k != key})
        super().__delitem__(key)
        self._propagate()


class sequence:
    def __setitem__(self, name, value):
        # deal with slices.
        super().__setitem__(name, value)

    def insert(self, *arg, **kwargs):
        super().insert(*arg, **kwargs)

    def append(self, *arg, **kwargs):
        super().append(*arg, **kwargs)

    def extend(self, *arg, **kwargs):
        super().extend(*arg, **kwargs)

    def __delitem__(self, key):
        super().__delitem__(key)


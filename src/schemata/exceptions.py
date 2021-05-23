from contextlib import suppress


class ValidationError(AssertionError, suppress):
    def __init__(self, *args, **kw):
        if AssertionError not in args:

            args += (AssertionError,) + args
        self.exceptions = tuple()
        suppress.__init__(self, *args)
        AssertionError.__init__(self, **kw)

    def __str__(self):
        import pprint

        if self.exceptions:
            return pprint.pformat(self.exceptions)
        return super().__str__()

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, type, exception, traceback):
        if type is exception is traceback is None:
            return
        self.exceptions += (exception,)

        return super().__exit__(type, exception, traceback)

    def raises(self):
        if self.exceptions:
            raise self
        return self

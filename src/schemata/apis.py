from functools import partialmethod


class StringCase:
    def _stringcase(self, case):
        import stringcase

        from .strings import String

        return String(getattr(stringcase, case)(self))

    for (
        k
    ) in "alphanumcase backslashcase camelcase camelcase constcase dotcase lowercase pascalcase pathcase sentencecase snakecase spinalcase titlecase trimcase uppercase".split():
        locals().update({k: partialmethod(_stringcase, k)})
    del k


class Statistics:
    pass

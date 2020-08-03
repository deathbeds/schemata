class unary:
    def __neg__(cls):
        return type(
            f"not{cls.__name__}",
            (cls,),
            dict(__annotations__=dict({"not": cls.__annotations__})),
        )

    def __pos__(cls):
        return cls


class binary:
    def __add__(cls, object):
        return type(cls.__name__ + object.__name__, (cls, object), {})

    def __sub__(cls, object):
        return cls + -object

    # def __mul__(cls, object):
    #     if isinstance(object, int):
    #         if cls.__annotations__['format'] == 'int'
    #     raise NotImplemented(F"__mul__ not implemented for type {cls}")

    def __and__(cls, object):
        import schemata

        return type(
            f"{cls.__name__}and{object.__name__}",
            (schemata.core.schema,),
            dict(allOf=[cls.__annotations__, object.__annotations__]),
        )

    def __and__(cls, object):
        import schemata

        return type(
            f"{cls.__name__}and{object.__name__}",
            (schemata.core.schema,),
            dict(allOf=[cls.__annotations__, object.__annotations__]),
        )

    def __xor__(cls, object):
        import schemata

        return type(
            f"{cls.__name__}and{object.__name__}",
            (schemata.core.schema,),
            dict(oneOf=[cls.__annotations__, object.__annotations__]),
        )

    def __ge__(cls, object):
        if isinstance(object, int):
            if issubclass(cls, (int, float)):
                key = "minimum"
            elif issubclass(cls, list):
                key = "minItems"
            elif issubclass(cls, dict):
                key = "minProperties"
            return type(cls.__name__, (cls,), dict(__annotations__={key: object}))
        raise NotImplemented(f"__ge__ not implemented for type {cls}")
    
    def __le__(cls, object):
        if isinstance(object, int):
            if issubclass(cls, (int, float)):
                key = "maximum"
            elif issubclass(cls, list):
                key = "maxItems"
            elif issubclass(cls, dict):
                key = "maxProperties"
            return type(cls.__name__, (cls,), dict(__annotations__={key: object}))
        raise NotImplemented(f"__le__ not implemented for type {cls}")

    def __gt__(cls, object):
        if isinstance(object, int):
            if issubclass(cls, (int, float)):
                key = "minimum"
            elif issubclass(cls, list):
                key = "minItems"
            elif issubclass(cls, dict):
                key = "minProperties"
            return type(cls.__name__, (cls,), dict(__annotations__={key: object}))
        raise NotImplemented(f"__gt__ not implemented for type {cls}")
    
    def __lt__(cls, object):
        if isinstance(object, int):
            if issubclass(cls, (int, float)):
                key = "maximum"
            elif issubclass(cls, list):
                key = "maxItems"
            elif issubclass(cls, dict):
                key = "maxProperties"
            return type(cls.__name__, (cls,), dict(__annotations__={key: object}))
        raise NotImplemented(f"__lt__ not implemented for type {cls}")

    def __getitem__(cls, object):
        if isinstance(object, type):
            return cls + object
        if isinstance(object, dict):
            return type(cls.__name__, (cls,), dict(__annotations__=object))
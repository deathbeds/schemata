"""various caches that schemata defines for improved performance."""
import collections


def cache(object):
    """a decorator to cache goes intos and goes out ofs

    the object is mapping that holds the cache"""
    import functools

    def wraps(callable):
        @functools.wraps(callable)
        def wrap(cls, *args):
            id = (cls,) + args
            try:
                # try to find the cls in the cache
                if id in object:
                    return object[id]
            except TypeError:
                # if the id isn't hashable do this
                return callable(cls, *args)
            # cache the id for reuse later
            object[id] = callable(cls, *args)
            return object[id]

        # if the type has a registration method then append that
        # to the wrap function
        if hasattr(callable, "register"):
            wrap._ = wrap.register = callable.register
        return wrap

    return wraps


__schemata__ = dict()
__strategies__ = dict()
# mro to type cache
__schemata_types__ = dict()
# python to schemata
__abc_types__ = collections.defaultdict(list)

schemata_cache = cache(__schemata__)
strategy_cache = cache(__strategies__)

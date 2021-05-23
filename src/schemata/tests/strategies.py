import hypothesis.strategies

from schemata import *
from schemata.utils import register, suppress


@register
def get_st(x):
    return hypothesis.strategies.just(x)


@get_st.register(list)
@get_st.register(tuple)
def get_st_iter(x):
    return hypothesis.strategies.one_of(map(get_st, x))


@get_st.register
def get_st_iter(x: hypothesis.strategies.SearchStrategy):
    return x


@get_st.register
def get_st_range(x: range):
    return hypothesis.strategies.integers(min_value=x.start, max_value=x.stop)


none = hypothesis.strategies.none()
literals = get_st((Null, Bool, Integer, Float, String))
containers = get_st((List, Dict))
composites = get_st((AllOf, AnyOf, OneOf))


@hypothesis.strategies.composite
def draw_schemata(draw, base=literals | containers, container=containers, i=get_st(1)):
    c = draw(container)
    id = draw(i)
    if c is None:
        return draw(base)
    if id > 1:
        return c[tuple(draw(base) for _ in range(id + 1))]

    return c[draw(base)]


types = draw_schemata()

complexes = draw_schemata(
    base=types,
    container=composites,
    i=hypothesis.strategies.integers(min_value=2, max_value=5),
)


@hypothesis.strategies.composite
def draw_type_value(draw, types):
    t = draw(types)
    return t, draw(t.strategy())

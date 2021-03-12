from schemata import *
import hypothesis, operator, pytest

false = (0, "", [], {})
true = (1.0, "a", ["a"], {"a": bool})
exceptions = Literal, Enum, Default, Const, Uri, File
spot_tests = [
    String > 2,
]

literals = [
    x
    for x in vars(literal).values()
    if isinstance(x, Generic) and x not in exceptions and not issubclass(x, Sys)
]

strings = [
    x
    for x in vars(strings).values()
    if isinstance(x, Generic)
    and x not in literals
    and x not in (Date, Time, IPv4, IPv6)
    and not issubclass(x, Pattern)
]


literals += [x for x in vars(numbers).values() if isinstance(x, Generic)]


jsons = [
    x
    for x in vars(json).values()
    if isinstance(x, Generic) and x not in literals + strings
]


@hypothesis.strategies.composite
def draw(
    draw,
    t=(
        hypothesis.strategies.sampled_from(spot_tests)
        | hypothesis.strategies.sampled_from(literals)
    ),
    n=hypothesis.strategies.integers(min_value=1, max_value=6),
    op=hypothesis.strategies.sampled_from(
        [
            operator.and_,
            operator.or_,
            operator.xor,
        ]
    ),
):
    x = None
    for _ in range(draw(n)):
        y = draw(t)
        x = y if x is None else draw(op)(x, draw(t))
    return x


@hypothesis.strategies.composite
def draw_enum(
    draw,
    a=hypothesis.strategies.lists(draw(), min_size=1),
):
    return Enum[[draw(x.strategy()) for x in draw(a)]]


@hypothesis.given(
    (
        draw()
        | draw_enum()
        | draw().map(lambda x: Dict[x])
        | draw().map(lambda x: List[x])
        | hypothesis.strategies.sampled_from(strings)
        | hypothesis.strategies.sampled_from(jsons)
    ).flatmap(
        lambda x: globals().__setitem__("G", x) or x.strategy().map(lambda y: (x, y))
    )
)
@hypothesis.settings(max_examples=200)
def test_literals(x):
    global T, V

    T, V = t, v = x
    if not issubclass(t, Generic.Alias):
        t()
    y = t.instance(v)
    assert y == v
    hypothesis.assume(not isinstance(v, (bool, type(None))))
    assert isinstance(y, t)
    assert Default[v].instance() == v
    assert Const[v].instance() == v
    assert (t + Default[v]).instance() == v
    # assert (t + Const[v]).instance() == v not really adding anything IMO


@hypothesis.given(
    (
        hypothesis.strategies.sampled_from(literals)
        | draw_enum()
        | draw().map(lambda x: Dict[x])
        | draw().map(lambda x: List[x])
    ).flatmap(
        lambda x: globals().__setitem__("G", x)
        or composite.Not[x].strategy().map(lambda y: (x, y))
    )
)
@hypothesis.settings(max_examples=100)
def test_null_space(v):
    import jsonschema
    import pytest

    global T, V
    T, V = t, v = v
    with pytest.raises((ValidationError, jsonschema.ValidationError)):
        t(v)


def test_none():
    assert Null() is Null(None) is None
    for x in (False,) + (0, "", [], {}):
        with pytest.raises(ValidationErrors):
            Null(x)


def test_bool():
    assert Bool() is bool() is Bool(False)
    assert Bool(True) is True
    for x in true + false:
        with pytest.raises(ValidationErrors):
            Bool(x)


def test_string():
    assert String() == str() == "" == String("")


def test_numbers():
    assert Float() == float() == 0.0 == Float(0.0)
    assert Integer() == int() == 0.0 == Integer(0.0)


def test_dict():
    assert Dict() == Dict({}) == dict() == {}
    with pytest.raises(ValidationErrors):
        assert dict("") == {}
        Dict("")


def test_list():
    assert List() == List([]) == list() == []
    with pytest.raises(ValidationErrors):
        assert list("") == []
        List("")

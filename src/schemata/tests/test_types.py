import functools
import operator
import unittest

import hypothesis
import jsonpatch
import pytest

from schemata import *


def unwrap(x):
    return getattr(getattr(x, "hypothesis", x), "inner_test", x)


def type_example(x):
    return x.strategy().map(lambda y: (x, y))


class LiteralTest(unittest.TestCase):
    examples = hypothesis.strategies.sampled_from((Null, Bool, Integer, Number, String))

    @hypothesis.given(examples.flatmap(type_example))
    def test_literals(self, t):
        t, v = t
        y = t.instance(v)
        assert y == v
        hypothesis.assume(not isinstance(v, (bool, type(None))))
        assert isinstance(y, t)
        assert Default[v].instance() == v
        assert Const[v].instance() == v
        assert (t + Default[v]).instance() == v

    def test_none(x):
        assert Null() is Null(None) is None
        for x in (False,) + (0, "", [], {}):
            with pytest.raises(ValidationErrors):
                Null(x)

    def test_bool(x):
        assert Bool() is bool() is Bool(False)
        assert Bool(True) is True
        for x in true + false:
            with pytest.raises(ValidationErrors):
                Bool(x)

    def test_string(x):
        assert String() == str() == "" == String("")
        assert String("abc") == str("abc") == "abc" == String("abc")

    def test_numbers(x):
        assert Float() == float() == 0.0 == Float(0.0)
        assert Integer() == int() == 0.0 == Integer(0.0)


false = (0, "", [], {})
true = (1.0, "a", ["a"], {"a": bool})


class MyDict(Dict):
    a: String
    b: String + Default["abc"]


class MyList(List + Generic.MinItems[1]):
    a: String
    b: String + Default["abc"]


class ContainerTest(unittest.TestCase):
    examples = (
        hypothesis.strategies.sampled_from((Dict, List, IDict, IList))
        | LiteralTest.examples.map(lambda x: Dict[x])
        | LiteralTest.examples.map(lambda x: List[x])
    )

    test_literals = hypothesis.given(examples.flatmap(type_example))(
        unwrap(LiteralTest.test_literals)
    )

    def test_dict(x):
        assert Dict() == Dict({}) == dict() == {}
        with pytest.raises(ValidationErrors):
            assert dict("") == {}
            Dict("")

        with pytest.raises(ValidationErrors):
            MyDict()

        assert MyDict("xxx") == MyDict(a="xxx") == dict(a="xxx", b="abc")

        d = Dict[List]()
        assert "a" not in d and d["a"] == dict(a=[])

    def test_list(x):
        assert List() == List([]) == list() == []
        with pytest.raises(ValidationErrors):
            assert list("") == []
            List("")

        with pytest.raises(ValidationErrors):
            MyList()

        with pytest.raises(ValidationErrors):
            MyList([])

        with pytest.raises(ValidationErrors):
            MyList([dict(b="xxx")])

        assert MyList([dict(a="a")]) == [dict(a="a")]


class ExoticTest(unittest.TestCase):
    @hypothesis.strategies.composite
    def examples(
        draw,
        t=ContainerTest.examples | LiteralTest.examples,
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

    examples = examples()

    @hypothesis.strategies.composite
    def draw_enum(
        draw,
        a=hypothesis.strategies.lists(examples, min_size=1),
    ):
        return Enum[[draw(x.strategy()) for x in draw(a)]]

    draw_enum = draw_enum()

    test_literals = hypothesis.given((examples).flatmap(type_example))(
        unwrap(LiteralTest.test_literals)
    )

    @hypothesis.given(
        (examples | draw_enum).flatmap(
            lambda x: globals().__setitem__("G", x)
            or Not[x].strategy().map(lambda y: (x, y))
        )
    )
    @hypothesis.settings(max_examples=100)
    def test_null_space(x, v):
        global T, V
        T, V = t, v = v
        with pytest.raises(ValidationErrors):
            t(v)


@hypothesis.strategies.composite
def draw_patches(
    draw,
    t=hypothesis.strategies.sampled_from(
        [
            IDict[dict(name=String)],
            IList[dict(name=String)],
        ]
    ),
    n=1,
) -> (List[Dict[dict(type=object, patch=list, value=dict)]]):
    import jsonpatch

    i, t = 0, draw(t)
    s = t.strategy()
    v = draw(s)
    patches = [dict(type=t, patch=[], value=v)]
    while i < n:
        v, b = draw(t.strategy()), v
        p = jsonpatch.make_patch(b, v).patch
        if p:
            i += 1
            patches.append(dict(type=t, patch=p, value=v))
    return patches


class PyTests(unittest.TestCase):
    def test_py(x):
        assert Sys["builtins.range"]() is range
        assert Py["builtins.range"]() is range

        with pytest.raises(TypeError):
            Instance["builtins.range"]()

        assert Instance["builtins.range"](10) == range(10)


class CastTests(unittest.TestCase):
    def test_py(x):
        with pytest.raises(ValidationErrors):
            Cast[Integer, String](1)
        assert Cast[Integer, str, String](10) == "10"


@hypothesis.given(draw_patches())
@hypothesis.settings(
    max_examples=20,
    suppress_health_check=[
        hypothesis.HealthCheck.large_base_example,
        hypothesis.HealthCheck.too_slow,
    ],
)
def test_patch(ps):
    import jsonpatch

    global P
    P = ps
    for i, p in enumerate(ps):
        if not i:
            x = p["type"](p["value"])
        else:
            with x:
                x.patches(*p["patch"])

        assert x == p["value"], f"{x}\n\n{p['value']}"


def test_juxt():
    assert Juxt["builtins.type"](int) == type
    assert Juxt["builtins.type".format](int) == "builtins.type"
    assert Juxt[type, range](1) == (int, range(1))
    assert Juxt[[type, range]](1) == [int, range(1)]
    assert Juxt[{type, range}](1) == {int, range(1)}
    assert Juxt[dict(a=type, b=range)](1) == {"a": int, "b": range(0, 1)}
    assert Juxt[{type: type, str: range}](1) == {int: int, "1": range(0, 1)}

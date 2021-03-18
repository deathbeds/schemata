import functools
import operator
import unittest

import hypothesis
import jsonpatch
import pytest

from schemata import *

raises = pytest.raises(ValidationErrors)


def unwrap(x):
    return getattr(getattr(x, "hypothesis", x), "inner_test", x)


def type_example(x):
    return x.strategy().map(lambda y: (x, y))


class BaseTest(unittest.TestCase):
    def test_base(x):
        assert Any.new_type() is Any

    def test_forward(x):
        assert Forward("builtins.range").instance() is range


class LiteralTest(unittest.TestCase):
    examples = hypothesis.strategies.sampled_from((Null, Bool, Integer, Number, String))

    @hypothesis.given(examples.flatmap(type_example))
    def test_literals(self, t):
        t, v = t
        assert t[:] is t
        y = t.instance(v)
        assert y == v
        hypothesis.assume(not isinstance(v, (bool, type(None))))
        assert isinstance(y, t)
        assert Default[v].instance() == v
        assert Const[v].instance() == v
        assert (t + Default[v]).instance() == v

    def test_none(x):
        Null(Null.example())
        assert Null() is Null(None) is None
        for x in (False,) + (0, "", [], {}):
            with pytest.raises(ValidationErrors):
                Null(x)

    def test_bool(x):
        Bool(Bool.example())

        assert Bool() is bool() is Bool(False)
        assert Bool(True) is True
        for x in true + false:
            with pytest.raises(ValidationErrors):
                Bool(x)

    def test_string(x):
        String(String.example())

        assert String() == str() == "" == String("")
        assert String("abc") == str("abc") == "abc" == String("abc")

    def test_numbers(x):
        Number(Number.example())
        Integer(Integer.example())

        assert Float() == float() == 0.0 == Float(0.0)
        assert Integer() == int() == 0.0 == Integer(0.0)

    def test_display(x):
        assert "application/json" in Json({})._repr_mimebundle_()[0]
        assert "text/plain" in String("")._repr_mimebundle_()[0]

    def test_enum(x):
        E = Enum["a", "b"]

        assert E() == "a"
        with raises:
            E("c")
        assert E("b") == "b"


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
        Dict(Dict.example())
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
        List(List.example())

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

    def test_ilist(x):
        L = IList[String]

        with raises:
            L(1)

        with raises:
            L("abc")

        l = (list >> L)("abc")

        assert isinstance(l, IList)

        with raises:
            l.append(1)

        l.append("d")

        assert l == list("abcd")

        with raises:
            l.extend([1, "a"])

        l.extend(list("ef"))
        assert l == list("abcdef")

        l.remove("a")
        assert l == list("bcdef")

        l.pop(0)
        assert l == list("cdef")

        assert l[0] == "c" and l[-1] == "f"

        l.pop()
        assert l[-1] == "e"

        with raises:
            m = l + [2, 4]

        m = l + list("yz")

        assert m == list("cdeyz")

        m.insert(3, "w")
        assert m == list("cdewyz")

        m[3] = "W"

        assert m == list("cdeWyz")

    def test_idict(x):
        D = IDict[String]

        with raises:
            D(a=1)

        d = D(a="A")
        assert d == dict(a="A") and d["a"] == d.get("a") == "A" and d.get("q") is None
        with raises:
            d["a"] = 1

        d["a"] = "B"
        assert d == dict(a="B") and d["a"] == "B"
        d.pop("a")
        assert not d

        d.update(b="B", c="C")

        assert d == dict(b="B", c="C")

        with raises:
            d.update(b="B", c="C", d=1)

        with raises:
            (D >= 1)()
        e = (D >= 1)(a="a")
        with raises:
            e.pop("a")
        assert e == dict(a="a")


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
        draw, a=examples, i=hypothesis.strategies.sampled_from([0, 1, 5, 20])
    ):

        return Enum[tuple(draw(draw(a).strategy()) for _ in range(draw(i)))]

    draw_enum = draw_enum()

    test_literals = hypothesis.given((examples).flatmap(type_example))(
        unwrap(LiteralTest.test_literals)
    )

    # @hypothesis.given(draw_enum)
    # def test_enums(x, t):
    #     c = t.choices()
    #     for x in c:
    #         t(c)
    #     hypothesis.assume(t.choices())
    #     assert t() is t.choices()[0]

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

    test_symbollic = hypothesis.given(
        hypothesis.strategies.sampled_from(
            (
                (String > 1) < 10,
                (String >= 1) <= 10,
                (Integer > 1) < 10,
                (Integer >= 1) <= 10,
                (Number > 1) < 10,
                (Number >= 1) <= 10,
                (Dict > 1) < 10,
                (Dict >= 1) <= 10,
                (List > 1) < 10,
                (List >= 1) <= 10,
                OneOf[Bool],
                OneOf[Null],
            )
        ).flatmap(type_example)
    )(unwrap(LiteralTest.test_literals))


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
                x.add_patches(*p["patch"])

        assert x == p["value"], f"{x}\n\n{p['value']}"


def test_juxt():
    assert Juxt["builtins.type"](int) == type
    assert Juxt["builtins.type".format](int) == "builtins.type"
    assert Juxt[type, range](1) == (int, range(1))
    assert Juxt[[type, range]](1) == [int, range(1)]
    assert Juxt[{type, range}](1) == {int, range(1)}
    assert Juxt[dict(a=type, b=range)](1) == {"a": int, "b": range(0, 1)}
    assert Juxt[{type: type, str: range}](1) == {int: int, "1": range(0, 1)}


class StringTest(unittest.TestCase):
    def test_uritemplate(x):
        t = UriTemplate(
            "https://api.github.com/search/issues?q={query}{&page,per_page,sort,order}"
        )
        assert callable(t)
        assert t(query="heart") == "https://api.github.com/search/issues?q=heart"

    def test_templates(x):
        assert Format["pos arg {}, kwarg {foo}"]("hi", foo=2) == "pos arg hi, kwarg 2"
        assert Dollar["kwarg $foo $bar"](foo=1, bar="hello") == "kwarg 1 hello"
        assert Jinja["kwarg {{foo}} {{bar}}"](foo=1, bar="hello") == "kwarg 1 hello"
        assert JsonE[{"foo": {JsonE.EVAL: "foo"}, "bar": {JsonE.EVAL: "bar"}}](
            foo=1, bar="hello"
        ) == {"foo": 1, "bar": "hello"}

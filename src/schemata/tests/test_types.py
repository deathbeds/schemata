import datetime
import functools
import operator
import unittest

import hypothesis
import jsonpatch
import pytest

from schemata import *
from schemata import base, util
from schemata.util import *

r = raises = pytest.raises(ValidationErrors)


def unwrap(x):
    return getattr(getattr(x, "hypothesis", x), "inner_test", x)


def type_example(x):
    return x.strategy().map(lambda y: (x, y))


class CallTest(unittest.TestCase):
    def test_call(x):
        assert identity(1) == 1
        assert identity(1, []) == 1
        assert call(range, 10) == range(10)
        assert call(1, 10) == 1


class SchemaTest(unittest.TestCase):
    def test_schema(x):
        assert (
            Dict[dict(a=Integer.minimum(0))].schema().ravel().new("/properties/a")
            == Integer
        )
        Generic.Required["a", "b"].schema().new("")
        Generic.Properties[dict(a=Integer)].schema().ravel().new()
        assert String[:] is String
        assert base.Plural.type() is base.Plural


class BaseTest(unittest.TestCase):
    def test_forward(x):
        assert Forward("builtins.range").object() is range
        with pytest.raises(ConsentException):
            Forward("abcde").object()
        assert Forward(range) is range
        v = Forward("builtins.range")

        assert v() is v() is range


class LiteralTest(unittest.TestCase):
    examples = hypothesis.strategies.sampled_from((Null, Bool, Integer, Number, String))

    @hypothesis.given(examples.flatmap(type_example))
    def test_literals(self, t):
        t, v = t
        assert t[:] is t
        y = t.object(v)
        assert y == v
        hypothesis.assume(not isinstance(v, (bool, type(None))))
        assert isinstance(y, t)
        # assert Const[v].object() == v
        assert (t + Default[v]).object() == v
        # assert Default[v].object() == v

    def test_none(x):
        Null(Null.example())
        assert Null() is Null(None) is None
        for x in (False,) + (0, "", [], {}):
            with raises:
                Null(x)

    def test_bool(x):
        Bool(Bool.example())

        assert Bool() is bool() is Bool(False)
        assert Bool(True) is True
        for x in true + false:
            with raises:
                Bool(x)

    def test_string(x):
        String(String.example())

        assert String() == str() == "" == String("")
        assert (
            String("abc")
            == str("abc")
            == "abc"
            == String("abc")
            == String("abc").loads()
        )

    def test_numbers(x):
        Number(Number.example())
        Integer(Integer.example())

        assert Float() == float() == 0.0 == Float(0.0)
        assert Integer() == int() == 0.0 == Integer(0.0)

    def test_enum(x):
        E = Enum["a", "b"]

        assert E.choices() == ("a", "b")
        assert E() == "a"
        with raises:
            E("c")
        assert E("b") == "b"

        assert Enum["a"]("a") == "a"

        with raises:
            Enum["a"]("b")

        C = Cycler["a", "b", "c"]
        assert Cycler.forms(C) == ("a", "b", "c")
        c = C()

        assert next(c) == "a" and next(c) == "b" and next(c) == "c" and next(c) == "a"


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
        hypothesis.strategies.sampled_from((Dict, List))
        | LiteralTest.examples.map(lambda x: Dict[x])
        | LiteralTest.examples.map(lambda x: List[x])
    )

    test_literals = hypothesis.given(examples.flatmap(type_example))(
        unwrap(LiteralTest.test_literals)
    )

    def test_dict(x):
        Dict(Dict.example())
        assert Dict() == Dict({}) == dict() == {}
        with raises:
            assert dict("") == {}
            Dict("")

        with raises:
            MyDict()

        assert MyDict(a="xxx") == dict(a="xxx", b="abc")

        d = Dict[List]()
        assert "a" not in d
        assert d["a"] == [] and d == dict(a=[])
        assert Dict.default(lambda: dict(a=11))() == dict(a=11)

        d = Dict[dict(a=Integer[1])].required("a")()

        with raises:
            d.pop("a")

        assert d.pop("b", 22) == 22

        d["b"] = 33

        assert d.pop("b") == 33

    def test_bunch(x):
        class T(Bunch):
            a: Integer
            b: String
            c: String

            def c(x: ["a", "b"]):
                return f"""{x.a} and {x.b}"""

        # build a type from this type for coverage
        assert T.schema().ravel().new("").schema()

        assert set(T.schema()["dependencies"]) == set(dict(c=list("ab")))

        t = T(a=123, b="abc")

        assert t.c == "123 and abc"

        t.a = 789

        assert t.c == "789 and abc"
        with raises:
            t.a = "abc"

        with raises:
            T(a="wyz", b="abc")

        t._q = 8
        assert "_q" not in t and t._q == 8

    def test_list(x):
        List(List.example())

        assert List() == List([]) == list() == []
        with raises:
            assert list("") == []
            List("")

        with raises:
            MyList()

        with raises:
            MyList([])

        with raises:
            MyList([dict(b="xxx")])

            assert MyList([dict(a="a")]) == [dict(a="a")]
        a = List.minItems(1)([1])

        with raises:
            a.pop()
        assert a == [1]
        with raises:
            a.remove(1)
        assert a.append(2) == [1, 2]
        assert a.remove(1) == [2]
        a.append(3)
        assert a.pop(-1) == 3
        a[-1] = 4
        assert a == [4]

        assert a.insert(-1, 2).append(3) == [2, 4, 3]

        a = List[String]()

        with raises:
            a.append(1)

        assert a.append("a") == ["a"]
        assert a.insert(0, "b") == ["b", "a"]

        a = List[Integer]([1])

        with raises:
            a[0] = "a"

        a[0] = 2

        assert a == [2]

        a = (Pipe[range, list] >> List[Integer])(10)

        with raises:
            a[2:4] = "abc"

        a[2:4] = reversed(a[2:4])

        assert a == [0, 1, 4, 5, 6, 7, 8, 9]

        del a[2]
        assert a == [0, 1, 5, 6, 7, 8, 9]

        assert List(list(range(10))).map(lambda x: str(x)) == list(map(str, range(10)))
        v = List[Integer]([-1, -2, 4, 5]).filter(lambda x: x < 0)
        assert v == [-1, -2] and v.__class__ == List[Integer]

        assert List[Integer]([-1, -2, 4, 5]).filter(lambda x: x < 0) == [-1, -2]


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
        kind = draw(a)

        return kind + Enum[tuple(draw(kind.strategy()) for _ in range(draw(i)))]

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
        (examples).flatmap(
            lambda x: globals().__setitem__("G", x)
            or Not[x].strategy().map(lambda y: (x, y))
        )
    )
    @hypothesis.settings(max_examples=100)
    def test_null_space(x, v):
        global T, V
        T, V = t, v = v
        with raises:
            t(v)

        assert not isinstance(v, t)

    test_symbollic = hypothesis.given(
        hypothesis.strategies.sampled_from(
            (
                String.minLength(1).maxLength(10),
                Integer.minimum(1).maximum(10),
                Integer.exclusiveMinimum(1).exclusiveMaximum(10),
                Number.minimum(1).maximum(10),
                Number.exclusiveMinimum(1).exclusiveMaximum(10),
                # Dict.minProperties(1).maxProperties(10),
                List.minItems(1).maxItems(10),
                Tuple[String, Integer],
                Tuple[Integer],
                Float - Integer,
                OneOf[Bool],
                OneOf[Null],
            )
        ).flatmap(type_example)
    )(unwrap(LiteralTest.test_literals))


# @hypothesis.strategies.composite
# def draw_patches(
#     draw,
#     t=hypothesis.strategies.sampled_from(
#         [
#             IDict[dict(name=String)],
#             IList[dict(name=String)],
#         ]
#     ),
#     n=1,
# ) -> (List[Dict[dict(type=object, patch=list, value=dict)]]):
#     import jsonpatch

#     i, t = 0, draw(t)
#     s = t.strategy()
#     v = draw(s)
#     patches = [dict(type=t, patch=[], value=v)]
#     while i < n:
#         v, b = draw(t.strategy()), v
#         p = jsonpatch.make_patch(b, v).patch
#         if p:
#             i += 1
#             patches.append(dict(type=t, patch=p, value=v))
#     return patches


class PyTests(unittest.TestCase):
    def test_py(x):
        assert Py["builtins.range"]() is range

        with pytest.raises(TypeError):
            Instance["builtins.range"]()

        assert Instance["builtins.range"](10) == range(10)


class PipeTests(unittest.TestCase):
    def test_py(x):
        with raises:
            Pipe[Integer, String](1)
        assert Pipe[Integer, str, String](10) == "10"

        assert (String << print)("abc") == "abc"
        assert (String >> print)("abc") is None

        assert (String >> list)("abc") == list("abc")
        s = String("abc")
        s += "de"
        assert s == "abcde"
        assert hash(Pipe[range, bool:str:list].schema().hashable())
        assert Pipe[range, bool:str:list](10) == list(map(str, filter(bool, range(10))))
        assert Pipe[:] is Pipe


# @hypothesis.given(draw_patches())
# @hypothesis.settings(
#     max_examples=20,
#     suppress_health_check=[
#         hypothesis.HealthCheck.large_base_example,
#         hypothesis.HealthCheck.too_slow,
#     ],
# )
# def test_patch(ps):
#     import jsonpatch

#     global P
#     P = ps
#     for i, p in enumerate(ps):
#         if not i:
#             x = p["type"](p["value"])
#         else:
#             with x:
#                 x.add_patches(*p["patch"])

#         assert x == p["value"], f"{x}\n\n{p['value']}"


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
        t = strings.UriTemplate(
            "https://api.github.com/search/issues?q={query}{&page,per_page,sort,order}"
        )
        assert t.uri(query="heart") == "https://api.github.com/search/issues?q=heart"

    # def test_templates(x):
    #     assert Format["pos arg {}, kwarg {foo}"]("hi", foo=2) == "pos arg hi, kwarg 2"
    #     assert Dollar["kwarg $foo $bar"](foo=1, bar="hello") == "kwarg 1 hello"
    #     assert Jinja["kwarg {{foo}} {{bar}}"](foo=1, bar="hello") == "kwarg 1 hello"
    #     assert JsonE[{"foo": {JsonE.EVAL: "foo"}, "bar": {JsonE.EVAL: "bar"}}](
    #         foo=1, bar="hello"
    #     ) == {"foo": 1, "bar": "hello"}


class PyTypeTest(unittest.TestCase):
    def test_pytypes(x):
        def f():
            pass

        import functools

        assert not isinstance(int, Py["functools.partial"])

        assert isinstance(functools.partial(f), Py["functools.partial"])

        assert Py["builtins.range"]() is range

        with pytest.raises(TypeError):
            Instance["builtins.range"]()

        assert Instance["builtins.range"](10) == range(10)
        assert isinstance(range(10), Instance["builtins.range"])

        import inspect
        import urllib

        # assert Instance["urllib.request.Request"].__signature__ == inspect.signature(
        #     urllib.request.Request
        # )
        assert Instance[Integer](10) == 10
        assert Instance[list]([1]) == [1]

        def g(a, b):
            return a, b

        assert Star[g](dict(a=1, b=2)) == (1, 2)

        assert Do[lambda x: None](10) is 10


class ManualTests(unittest.TestCase):
    def test_init(x):
        import math

        assert Null(None) is None
        assert Bool(True) is True
        assert Bool(False) is False
        assert Integer(10) == 10
        assert Float(math.pi) == math.pi
        assert String("abc") == "abc"
        assert List([1, 2]) == [1, 2]
        assert Dict(dict(a=11)) == dict(a=11)

        assert Py["builtins.range"]() is range

        assert Instance["builtins.range"](10) == range(10)
        assert Pipe["builtins.range", "builtins.list"](10) == list(range(10))
        import math

        assert Null(None) is None
        assert Bool(True) is True
        assert Bool(False) is False
        assert Integer(10) == 10
        assert Float(math.pi) == math.pi
        assert String("abc") == "abc"
        assert List([1, 2]) == [1, 2]
        assert Dict(dict(a=11)) == dict(a=11)
        with raises:
            Dict([])

        with raises:
            List({})

        assert isinstance((List | Dict)([]), List)
        assert isinstance((List | Dict)({}), Dict)
        assert isinstance((List ^ Dict)([]), List)
        assert isinstance((List ^ Dict)({}), Dict)

        assert isinstance(Json([]), List)

        assert isinstance(Json({}), Dict)

        assert isinstance(Json(1), Number)

        assert isinstance(Json(None), Null)

        with raises:
            base.Minimum[0](-1)

        assert base.Minimum[0](1) is 1
        with raises:
            Dict[dict(a=Integer)](a="abc")

        with raises:
            (Integer >> String)(1)

        assert (Integer >> str >> String)(1) == "1"

    def test_null(x):
        assert Null() is None is Null(None) is (Null + Const[None])() is Null[None]()
        with r:
            Null(1)

    def test_bool(x):
        assert Bool() is False is bool() is Bool(False) is Bool[False]()
        assert Bool(True) is True is bool(True) is Bool[True]()
        with r:
            Bool(1)

    def test_number(x):
        assert Number() == float() == 0
        assert Number(1.1) == float(1.1) == 1.1 == Number[1.1]()
        assert Number(1) == float(1) == 1 == Number[1]()
        with r:
            Number("abc")

    def test_integer(x):
        assert Integer() == int() == 0
        with r:
            Integer(1.1)
        assert Number(1) == int(1) == 1 == (Number + Const[1])()
        with r:
            Number("abc")

    def test_string(x):
        assert String() == str() == ""
        with r:
            String(123)
        assert String("abc") == "abc"
        with raises:
            String.minLength(3)("ab")
        assert String.minLength(3)("abc") == "abc"
        assert String.maxLength(3)("abc") == "abc"
        with raises:
            String.maxLength(3)("abcd")
        with raises:
            base.Pattern["^foo"]("bar")
        assert isinstance("this", String.pattern("^this"))
        assert not isinstance("his", String.pattern("^this"))
        assert base.Pattern["^foo"]("foo bar") == "foo bar"
        assert strings.DateTime("2018-11-13T20:20:39+00:00") == __import__(
            "datetime"
        ).datetime(2018, 11, 13, 20, 20, 39)

        assert strings.Time("20:20:39+00:00") == datetime.datetime(
            1970, 1, 1, 20, 20, 39
        )

        assert strings.Date("2001-01-01") == datetime.datetime(2001, 1, 1, 0, 0)

        with raises:
            strings.Email("")

        assert strings.Email("@") == "@"
        assert strings.UriTemplate(
            "https://api.github.com/search/labels?q={query}&repository_id={repository_id}{&page,per_page}"
        )

        assert strings.UriTemplate("") == ""

        with raises:
            strings.Regex("(Yfoo")

        import re

        assert strings.Regex("^foo") == re.compile("^foo")

        assert strings.Pointer("a", "b") == "/a/b"

        assert strings.Yaml("a: b").loads() == dict(a="b")

        assert strings.Toml("a = 'b'").loads() == dict(a="b")

        assert strings.JsonString('{"a": "b"}').loads() == dict(a="b")

        assert isinstance(strings.Markdown("# this").loads(), Generic.ContentMediaType)

    def test_default(x):
        # only going to return the default value
        assert Default[1](2) == 1
        assert Default[1]() == 1
        assert Default[lambda: 1]() == 1

    def test_list(x):
        assert List() == [] == list()
        assert List(list("abc")) == list("abc")
        with r:
            List("abc")

        t = List[String]
        with r:
            t([1, 2, 3])
        v = t(list("abc"))
        with r:
            v.append(1)
        assert v == list("abc")

        assert v.append("d") == list("abcd")
        with r:
            v.append(1)
        with r:
            v + [1]

        assert (v + list("ef")) == list("abcdef")

        assert List[Integer, String]((1, "abc")) == [1, "abc"]
        assert List[Integer, String]((1,)) == [1]

        with r:
            List[Integer, String]([1, 2])
        assert (
            type(List[Integer](list(range(10))).groupby(type))
            == Dict[type, List[Integer]]
        )

        with r:
            List[Integer](list(range(10))).map(String)

    def test_dict(x):
        assert Dict() == {} == dict()
        v = dict(a=1, b="abc")
        assert Dict(v) == v
        with r:
            Dict[Integer](v)

        class T(Dict):
            z: String = "abc"
            w: Float
            y: Integer
            x: String
            v: List

            def y(x: "w"):
                return int(x["w"])

            def x(x: "y"):
                return str(x["y"])

            def v(x: "x"):
                return list(x["x"])

        s = T.schema()
        globals().update(locals())
        assert all(map(s.__contains__, "dependencies required properties".split()))
        with r:
            T()
        i = 99.999
        t = T(w=i)
        assert t["w"] == i
        i = 12.3456
        t["w"] = i
        assert t["w"] == i
        with r:
            t["w"] = "abc"
        t = Dict[int, Integer]
        with r:
            t(dict(a=1))
        assert t({1: 1}) == {1: 1}

        assert Dict[dict(a=Integer[1])]() == dict(a=1)
        assert Dict(a=1).map(str).map(String).__class__ == Dict[String]

        with raises:
            base.Required["a"](dict())

        assert base.Required["a"](dict(a=11)) == dict(a=11)
        assert (Dict[dict(bar=Integer)] >> strings.Jinja["foo {{bar}}"])(
            bar=11
        ) == "foo 11"
        assert len(OneOf.forms(Json)) == 6
        v = dict(zip("abc", range(3)))
        assert Dict(v).map(str) == dict(zip(v.keys(), map(str, v.values())))
        assert Dict(v).map(Integer).__class__ == Dict[Integer]

        assert Dict(v).filter(lambda x: x > 1) == dict(c=2)

        assert Dict(v).map(str.upper, None) == dict(
            zip(map(str.upper, v.keys()), v.values())
        )
        assert Dict(v).map(str.upper, str) == dict(
            zip(map(str.upper, v.keys()), map(str, v.values()))
        )

        assert Dict(dict(zip(map(str, range(3)), range(3)))).filter(
            "1".__eq__, (1).__eq__
        ) == {"1": 1}
        assert Dict(dict(zip(map(str, range(3)), range(3)))).filter(
            "1".__eq__, None
        ) == {"1": 1}
        assert (
            Dict(dict(zip(map(str, range(3)), range(3)))).filter("1".__eq__, (2).__eq__)
            == {}
        )

        v = dict(zip([1, "a", 3], list("abc")))
        assert Dict(v).map(String ^ Integer, String) == v and isinstance(
            Dict(v).map(String ^ Integer, String), Dict[String ^ Integer, String]
        )
        assert Dict(v).map(String ^ Integer, None) == v and isinstance(
            Dict(v).map(String ^ Integer, String), Dict[String ^ Integer, None]
        )

    def test_abc(x):
        assert Dict.type != List.type != base.Type.type
        assert not issubclass(Dict, Dict.Keys)
        assert not issubclass(Dict, Generic.Nested)
        assert issubclass(String["abc"], Default)
        with raises:
            (-String)("abc")
        assert (-String)(1) == 1
        assert (+String) is String
        assert isinstance(Generic.Items.forms(Tuple[[int, str]]), tuple)
        # this might not be right...
        assert issubclass(Dict.MinProperties[3], Dict.minProperties(3))
        assert Dict.type() is Dict
        assert base.Type.type() is base.Type
        assert base.Type.type() is base.Type
        with raises:
            (Integer ^ Number)(1)

        assert (Integer ^ Number)(1.1) == 1.1

    def test_just(x):
        assert Juxt[range](10) == range(10)

        assert Juxt[range, type](10) == (range(10), int)

        assert Juxt[[range, type]](10) == [range(10), int]

        assert Juxt[{range, type}](10) == {range(10), int}

        assert (range >> Juxt[(lambda x: x % 2) : str : list])(10) == list(
            map(str, range(1, 10, 2))
        )


class FileTest(unittest.TestCase):
    def test_file(x):
        assert isinstance(Dir(""), Path) and isinstance(Dir(""), base.Type)
        assert isinstance(File(""), Path) and isinstance(File(""), base.Type)


def test_if():
    t = If[String : String.maxLength(3) : Integer]
    assert t("abc") == "abc"
    assert t(11) == 11
    with raises:
        t("abcd")
    with raises:
        t(2.2)

    with raises:
        If[Integer::String](1.1)

    assert If[Integer::String](1) == 1


def test_file(pytester):
    pytester.makefile(".yaml", tester="a: b")
    s = File("tester.yaml").read()
    assert isinstance(s, str)
    assert s.loads() == dict(a="b")
    pytester.makefile(".txt", tester="a file")
    assert File.read("tester.txt") == "a file"


def test_environ():
    import os

    assert Environ.type() is Environ
    assert Environ["FOO"]() is None
    assert "FOO" not in os.environ
    assert Environ["FOO", "123"]() == "123"

    assert "FOO" in os.environ


def test_sig():
    def f(*, bar, foo, **kwargs):
        pass

    from schemata import compat

    assert compat.get_signature(
        strings.Fstring["the {foo} is {bar}"].schema()["pattern"]
    ) == inspect.signature(f)

    class T(Dict):
        z: String = "abc"
        w: Float
        y: Integer
        x: String
        v: List

        def y(x: "w"):
            return int(x["w"])

        def x(x: "y"):
            return str(x["y"])

        def v(x: "x"):
            return list(x["x"])

    def f(w: Number, *, z: String["abc"] = "abc"):
        pass

    assert compat.get_signature(T) == inspect.signature(f)


def _typer_doctest():
    """
    >>> with suppress(SystemExit): apps.Typer[Dict[dict(a=Integer.minimum(0).maximum(10))]].help()
    Usage: ... [OPTIONS]...
    Options:
      --a INTEGER RANGE  [required]
      -h, --help         Show this message and exit.


    >>> with suppress(SystemExit): apps.Typer[Dict[dict(a=Integer.minimum(0).maximum(10))]].run("--a 5")
    {'a': 5}"""


def test_uri():
    from unittest import mock

    import requests

    t = strings.UriTemplate("https://{name}.com")
    assert "https://test.com" == t.uri(name="test")

    r = requests.Response()
    r.url = t.uri(name="test")
    with mock.patch("requests.get", return_value=r) as request:
        assert Uri().get() == r


def test_pointer():
    v = dict(a=[None, dict(b=2)])
    assert strings.Pointer("a") == "/a"

    assert strings.Pointer("a", 1, "b") == "/a/1/b"

    assert strings.Pointer() == ""
    assert strings.Pointer().resolve(v) == v
    assert strings.Pointer("a").resolve(v) == v["a"]
    assert strings.Pointer("a", 1).resolve(v) == v["a"][1]
    assert strings.Pointer("a", 1, "b").resolve(v) == v["a"][1]["b"]
    assert (strings.Pointer("/a/1") / "b").resolve(v) == v["a"][1]["b"]


def test_parse():
    p = strings.Parse["this {} is {name}"]

    assert p(11, name=9).schema().ravel() == {
        "type": "string",
        "pattern": "\\Athis (.+?) is (?P<name>.+?)\\Z",
    }

    assert issubclass(p.py(), typing.Pattern)

    assert p(11, name=9) == "this 11 is 9"


def test_load_dump():
    assert strings.Toml.dumps(dict(a="b")) == 'a = "b"\n'
    assert strings.Toml('''a = "b"''').loads() == dict(a="b")
    assert strings.Yaml("""a: b""").loads() == dict(a="b")
    assert strings.Yaml.dumps(dict(a="b")) == "a: b\n"
    assert strings.JsonString("""{"a": "b"}""").loads() == dict(a="b")
    assert strings.JsonString.dumps(dict(a="b")) == '{"a": "b"}'
    assert strings.JsonString("""{"a": "b"}""").loads() == dict(a="b")


def test_ensure_mro_c3():
    [
        functools._c3_mro(x)
        for x in (Null, Bool, Integer, Number, String, List, Dict, Dict[List], Json)
    ]


def test_typer():
    nil = "00000000-0000-0000-0000-000000000000"

    class CLI(Dict):
        arg_number: Number
        arg_number_min_max: Number.minimum(0).maximum(10)
        arg_number_clamp_min_max: Number.exclusiveMinimum(0).exclusiveMaximum(10)
        arg_bool: Bool
        arg_uuid: Uuid
        arg_datetime: strings.DateTime
        arg_enum: Enum["a", "b"]
        arg_file: File
        arg_multiple_list: List[Integer]
        arg_multiple_tuple: Tuple[String, File]

        opt_number: Number[0]
        opt_number_min_max: Number[0].minimum(0).maximum(10)
        opt_number_clamp_min_max: Number[0].exclusiveMinimum(0).exclusiveMaximum(10)
        opt_bool: Bool[True]
        opt_uuid: Uuid[nil]
        opt_datetime: strings.DateTime["2020-01-01"]
        opt_enum: Enum["a", "b", "c"] = "a"
        opt_file: File["readme.md"]
        arg_multiple_list: List[Integer] + Default[[1]]

        opt_multiple_tuple: Tuple[String, File] + Default["", "readme.md"]

    with pytest.raises(SystemExit):
        apps.Typer[CLI].help()

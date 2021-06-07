from schemata import *


def test_empty():
    assert not utils.EMPTY


def test_validates():
    class tester:
        @utils.validates(str)
        def f(self, object):
            return object

    assert tester.f("abc") == "abc"
    assert tester.f(1.1) is None


def test_enforce_type():
    assert isinstance(utils.enforce_tuple(1), tuple)
    assert not utils.enforce_tuple(None)


def test_merge():
    assert utils.merge(1) == {}
    assert utils.merge((dict(type="integer"), dict(type="number"))) == dict(
        type=("integer", "number")
    )
    assert (AllOf[Type[int]] + AllOf[Type[int]]).schema() == AllOf[Type[int]].schema()


def test_case():
    assert utils.lowercase("ABCD") == "aBCD"
    assert utils.uppercase(utils.lowercase("ABCD")) == "ABCD"
    assert not utils.lowercase("")


def test_normalize():
    assert utils.normalize_json_key("UiWidget") == "ui:widget"
    assert utils.normalize_json_key("Schema_") == "$schema"
    assert utils.normalize_json_key("Context__") == "@context"


# def test_docstring():
#     # comments
#     class Thing(Type, Examples[1, "abc"]):
#         """docstring"""

#     print(utils.get_docstring(Thing))
#     assert (
#         utils.get_docstring(Thing)
#         == """\
# docstring

# Notes
# -----
# comments


# Examples
# --------
# >>> Thing(1)
# 1
# >>> Thing("abc")
# 'abc'"""
#     )


def test_get_schemata():
    assert utils.get_schemata(None) is None
    assert utils.get_schemata(True) is True

    assert isinstance(utils.get_schemata("abc"), String)
    assert isinstance(utils.get_schemata(1), Integer)
    assert isinstance(utils.get_schemata(1.1), Float)

    assert isinstance(utils.get_schemata([]), List)
    assert isinstance(utils.get_schemata({}), Dict)

    assert utils.get_schemata("string") is String

    assert utils.get_schemata(None, cls=Type) is None


def test_derivation(pytester):
    import json

    class MyStuff(Dict):
        files: List[String]
        name: String
        id: Uri

    pytester.makefile(".jsonschema", my_stuff=json.dumps(MyStuff.schema(True)))

    derived = Any.from_schema(MyStuff.schema(True))

    from_file = Any.from_file("my_stuff.jsonschema")

    # assert {MyStuff: "our new type can reference the orgiinal"}.get(derived)
    assert from_file is not derived is not MyStuff

    # class OurStuff(Any.from_schema(MyStuff.schema(True))):
    #     pass

    # assert OurStuff == MyStuff == derived == from_file

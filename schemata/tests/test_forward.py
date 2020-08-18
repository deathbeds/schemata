import schemata.pytypes


def test_pandas():
    import pandas

    assert isinstance(pandas.DataFrame(), schemata.pytypes.DataFrame)


def test_forward():
    """Forward references have to evaluate to types so we can't use expressions."""
    with pytest.raises(TypeError):
        schemata.py["(builtins.int, builtins.float)"].__forward_reference__._evaluate(
            sys.modules, sys.modules
        )


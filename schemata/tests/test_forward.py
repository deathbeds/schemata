import schemata.pytypes


def test_pandas():
    import pandas
    assert isinstance(pandas.DataFrame(), schemata.pytypes.DataFrame)

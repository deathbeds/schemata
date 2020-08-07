import schemata


def _test_pandas():
    df = __import__("pandas").util.testing.makeDataFrame()
    assert isinstance(df, schemata.protocols.dataframe)
    assert isinstance(df.values, schemata.protocols.numpy)
    assert not isinstance(df, schemata.protocols.series)

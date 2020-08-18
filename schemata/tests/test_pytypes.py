from schemata.pytypes import *
import abc


def test_weakrefs():
    assert abc._get_dump(DataFrame)[0]


def test_dataframes():
    import pandas, dask.dataframe

    assert issubclass(pandas.DataFrame, DataFrame) and issubclass(
        dask.dataframe.DataFrame, DataFrame
    )

    assert isinstance(pandas.DataFrame(), DataFrame) and isinstance(
        dask.dataframe.from_pandas(pandas.util.testing.makeDataFrame(), 1), DataFrame,
    )


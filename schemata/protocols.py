import typing
from . import core

class numpy(core.protocol):
    data: typing.Iterable
    dtype: object

class series(core.protocol):
    values: typing.Iterable
    index: typing.Iterable
    dtype: object

class dataframe(core.protocol):
    values: typing.Iterable
    index: typing.Iterable
    dtypes: object
    columns: typing.Iterable

class value_widget(core.protocol):
    value: object
    description: str
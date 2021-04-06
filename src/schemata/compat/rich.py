import functools
import typing

import schemata


@functools.singledispatch
def get_rich(x, **k):
    if isinstance(x, schemata.Py["pandas.DataFrame"]):
        return get_rich_pandas(x)
    return str(x)


@get_rich.register
def get_rich_str(str: str, tree=None):
    if isinstance(str, schemata.base.ContentMediaType["text/markdown"]):
        return get_rich_markdown(str)
    return str


@get_rich.register
def get_rich_dict(dict: dict, tree=None):
    import rich.tree

    p = schemata.base.Properties.forms(dict)
    for k, v in p.items():
        if not isinstance(dict[k], p[k]):
            dict[v] = p[k](dict[k])

    a = schemata.base.AdditionalProperties.forms(dict)
    if a is not None:
        for k, v in dict.items():
            if k in p:
                continue
            dict[k] = a(dict[k])
    if tree is None:
        tree = rich.tree.Tree(get_rich(type(dict)))
    for key, value in dict.items():
        tree.add(rich.tree.Tree(label=key))
        tree.children[-1].add(get_rich(value))
    return tree


@get_rich.register
def get_rich_list(list: list, tree=None):
    import rich.tree

    if all(isinstance(item, dict) for item in list):
        return get_rich_table(list)
    if tree is None:
        tree = rich.tree.Tree(str(type(list)))
    for item in list:
        tree.add(get_rich(item))
    return tree


def get_rich_table(list: typing.List[dict]):
    import rich.table

    table = rich.table.Table()
    columns: set = functools.reduce(set.union, map(set, list))
    for column in columns:
        table.add_column(column)

    for item in list:
        table.add_row(*map(get_rich, map(item.get, columns)))

    return table


def get_rich_markdown(x, **k):
    import rich.markdown

    return rich.markdown.Markdown(x)


def get_rich_code(str, **k):
    import rich.syntax

    return rich.syntax.Syntax(str, str.language, line_numbers=True)


def get_rich_pandas(df, table=None, **k):
    if table is None:
        table = rich.table.Table()
    indexes = df.index.names
    columns = indexes + list(df.columns)
    for column in columns:
        table.add_column(column)
    for index, row in df.iterrows():
        if not isinstance(index, tuple):
            index = (index,)
        data = dict(zip(list(indexes), map("[b]{}".format, index)), **row)
        table.add_row(*map(get_rich, map(data.get, columns)))
    return table

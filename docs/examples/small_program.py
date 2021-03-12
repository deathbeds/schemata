import schemata.app

from schemata import *
import rich.markdown
import pandas

t = Dict[dict(name=S.String > 3)]
t >>= Jinja[
    """
# hello {{name}}, welcome to my program!

- this is some stuff

{{pandas.util.testing.makeDataFrame().to_markdown()}}
"""
]
t >>= rich.markdown.Markdown
t >>= rich.print

if __name__ == "__main__":
    import schemata.app

    schemata.app.Application[t].instance()

from schemata import *


FILE = Dict[dict(file=String)]["file"]
URL = Dict[dict(url=Uri, title=String)]["url"]
GLOB = Dict[dict(glob=String)]["glob"]

ENTRY = FILE | URL | GLOB


class Part(Dict):
    caption: String
    chapters: List[ENTRY]


class Book(Dict):

    format: Const["jb-book"]
    root: String
    chapters: List[ENTRY]
    parts: List[Part]


class Article(Dict):

    format: Const["jb-article"]
    root: String
    sections: List[ENTRY]

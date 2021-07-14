from schemata import *


class Setuptools(Dict):
    class Metadata(Dict):
        name: String
        version: String
        description: String
        long_description: String
        keys: String.comment_("comma separated")
        license: String
        classifiers: List

    class Options(Dict):
        zip_safe: Bool = False

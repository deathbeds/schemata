from schemata import *


class Setuptools(Dict):
    class Metadata(Dict):
        name: String
        version: String
        description: String
        long_description: String
        keys: String  # .comment_("comma separated")
        license: String
        classifiers: List

    class Options(Dict):
        zip_safe: Bool = False
        include_package_data: Bool
        packages: String = "find:"
        scripts: List
        install_requires: List
        package_data: Dict
        entry_points: Dict[Dict]
        extras_require: Dict
        packages: Dict[dict(find=Dict[dict(exclude=List)])]
        data_files: Dict

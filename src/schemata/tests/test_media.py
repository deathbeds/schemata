from rich import print

from schemata import *

sample_data = dict(a=1)


def test_toml(pytester):
    import toml

    pytester.makefile(".toml", sample=toml.dumps(sample_data))
    assert File.toml()("sample.toml").load() == sample_data


def test_json(pytester):
    import json

    pytester.makefile(".json", sample=json.dumps(sample_data))
    assert File.json()("sample.json").load() == sample_data


def test_yaml(pytester):
    import yaml

    pytester.makefile(".yaml", sample=yaml.safe_dump(sample_data))
    assert File.yaml()("sample.yaml").load() == sample_data

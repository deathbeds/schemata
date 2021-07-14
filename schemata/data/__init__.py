from .. import utils
import json

root = utils.Path(__file__).parent


def load(x):
    return json.loads((root / x).with_suffix(".json").read_text())


applicator = load("applicator")
validation = load("validation")
unevaluated = load("unevaluated")
format_assertion = load("format-assertion")
format_annotation = load("format-annotation")
content = load("content")
meta_data = load("meta-data")

jsonschema = utils.merge(
    applicator,
    validation,
    unevaluated,
    format_assertion,
    format_annotation,
    content,
    meta_data,
)

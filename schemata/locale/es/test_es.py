import hypothesis
import schemata.locale.es
import pytest
import jsonschema

def test_basic():
    with pytest.raises(jsonschema.exceptions.ValidationError):
        schemata.locale.es.objeto([])
    assert not schemata.locale.es.objeto({})

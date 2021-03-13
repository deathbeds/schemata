from . import protocols as P
from . import types as T

PositiveInteger = (T.Integer > 0).annotate(P.XSD["positiveInteger"])

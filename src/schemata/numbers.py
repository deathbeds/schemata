from . import literal as L
from . import protocols as P

PositiveInteger = (L.Integer > 0).annotate(P.XSD["positiveInteger"])

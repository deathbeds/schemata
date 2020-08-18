from .forward import py
import abc

class Array(abc.ABC):
    ...

Array.register(py['numpy.ndarray'])

class Series(abc.ABC):
    ...

Series.register(py['pandas.Series'])
Series.register(py['dask.dataframe.Series'])


class DataFrame(abc.ABC):
    ...

# these variables must persist for the 
# abcmeta to work since they are weakrefs
# they are destroyed if they aren't named
for key in 'pandas.DataFrame dask.dataframe.DataFrame'.split():
    locals()[key] = py[key]
    DataFrame.register(locals()[key])
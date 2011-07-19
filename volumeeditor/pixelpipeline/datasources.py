from PyQt4.QtCore import QObject, pyqtSignal

class Request( object ):
    def wait( self ):
        pass
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        pass

class DataSource( QObject ):
    # ranges
    changed = pyqtSignal( object )

    def request( self, slicing ):
        pass

    def put( self, slicing, value ):
        pass



class ArrayRequest( object ):
    def __init__( self, result ):
        self._result = result

    def wait( self ):
        return self._result
        
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        callback(self._result, **kwargs)

class ArrayDataSource( QObject ):
    changed = pyqtSignal( object )

    def __init__( self, array ):
        self._array = array

    def request( self, slicing ):
        return ArrayRequest(self._array[slicing])


class LazyflowRequest( object ):
    def __init__(self, lazyflow_request ):
        self._lazyflow_request = lazyflow_request
    def wait( self ):
        return self._lazyflow_request.wait()
    def notify( self, callback, **kwargs ):
        self._lazyflow_request.notify( callback, **kwargs)

class LazyflowDataSource( QObject ):
    changed = pyqtSignal( object )

    def __init__( self, operator, outslot = "Output" ):
        super(LazyflowReadDataSource, self).__init__()
        self._op = operator
        self._outslot = outslot

        self.data = None

    def _emitter(self, slicing ):
        self.changed.emit( slicing )

    def request( self, slicing ):
        reqobj = self._op.outputs[self._outslot][slicing].allocate()        
        return Request( reqobject )




if __name__ == '__main__':
    import numpy as np
    a = np.ones((123,213,212))
    ds = ArrayDataSource( a )
    slicing = (slice(10,20), slice(20,25), slice(10,30))
    print ds.request(slicing).wait()

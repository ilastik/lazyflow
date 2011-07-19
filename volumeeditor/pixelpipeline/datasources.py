from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import RequestABC, ArraySourceABC

class ArrayRequest( object ):
    def __init__( self, result ):
        self._result = result

    def wait( self ):
        return self._result
        
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        callback(self._result, **kwargs)
RequestABC.register(ArrayRequest)
assert issubclass(ArrayRequest, RequestABC)

class ArraySource( QObject ):
    def __init__( self, array ):
        self._array = array

    def request( self, slicing ):
        return ArrayRequest(self._array[slicing])
ArraySourceABC.register( ArraySource )
assert issubclass(ArraySource, ArraySourceABC)



class LazyflowRequest( object ):
    def __init__(self, lazyflow_request ):
        self._lazyflow_request = lazyflow_request

    def wait( self ):
        return self._lazyflow_request.wait()

    def notify( self, callback, **kwargs ):
        self._lazyflow_request.notify( callback, **kwargs)
RequestABC.register(LazyflowRequest)
assert issubclass(LazyflowRequest, RequestABC)

class LazyflowSource( QObject ):
    def __init__( self, operator, outslot = "Output" ):
        super(LazyflowSource, self).__init__()
        self._op = operator
        self._outslot = outslot

    def request( self, slicing ):
        reqobj = self._op.outputs[self._outslot][slicing].allocate()        
        return Request( reqobject )
ArraySourceABC.register( LazyflowSource )
assert issubclass(LazyflowSource, ArraySourceABC)






import unittest as ut
class ArraySourceTest( ut.TestCase ):
    def setUp( self ):
        import numpy as np
        self.np = np
        from scipy.misc import lena
        self.lena = lena()

        raw = np.zeros((1,512,512,1,1))
        raw[0,:,:,0,0] = self.lena
        self.source = ArraySource( raw )

    def testRequestWait( self ):
        slicing = (0,slice(10,20), slice(20,25), 0, 0)
        requested = self.source.request(slicing).wait()
        self.assertTrue(self.np.all(requested == self.lena[10:20, 20:25]))

    def testRequestNotify( self ):
        slicing = (0,slice(10,20), slice(20,25), 0, 0)
        request = self.source.request(slicing)
        
        def check(result, codon):
            self.assertTrue(self.np.all(result == self.lena[10:20, 20:25]))
            self.assertEqual(codon, "unique")
        request.notify(check, codon="unique")






if __name__ == '__main__':
    ut.main()

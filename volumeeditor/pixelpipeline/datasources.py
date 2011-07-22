from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import RequestABC, ArraySourceABC

def is_pure_slicing( slicing ):
    '''Test if slicing is a single slice or sequence of slices.

    Impure slicings may additionally contain integer indices, 
    ellipses, booleans, or newaxis.
    '''
    if isinstance(slicing, slice):
        return True
    if not hasattr(slicing, '__iter__'):
        return False
    for thing in slicing:
        if not isinstance(thing, slice):
            return False
    return True



class ArrayRequest( object ):
    def __init__( self, result ):
        self._result = result

    def wait( self ):
        return self._result
        
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        callback(self._result, **kwargs)
assert issubclass(ArrayRequest, RequestABC)

class ArraySource( QObject ):
    isDirty = pyqtSignal( object )

    def __init__( self, array ):
        super(ArraySource, self).__init__()
        self._array = array

    def request( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('ArraySource: slicing is not pure')
        assert(len(slicing) == len(self._array.shape)), \
            "slicing into an array of shape=%r requested, but the slicing object is %r" % (slicing, self._array.shape)
        return ArrayRequest(self._array[slicing])

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
assert issubclass(ArraySource, ArraySourceABC)



class LazyflowRequest( object ):
    def __init__(self, lazyflow_request ):
        self._lazyflow_request = lazyflow_request

    def wait( self ):
        return self._lazyflow_request.wait()

    def notify( self, callback, **kwargs ):
        self._lazyflow_request.notify( callback, **kwargs)
assert issubclass(LazyflowRequest, RequestABC)

class LazyflowSource( QObject ):
    isDirty = pyqtSignal( object )

    def __init__( self, operator, outslot = "Output" ):
        super(LazyflowSource, self).__init__()
        self._op = operator
        self._outslot = outslot

    def request( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('ArraySource: slicing is not pure')
        reqobj = self._op.outputs[self._outslot][slicing].allocate()        
        return LazyflowRequest( reqobj )

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
assert issubclass(LazyflowSource, ArraySourceABC)






import unittest as ut
from abc import ABCMeta, abstractmethod
class GenericArraySourceTest:
    __metaclass__ = ABCMeta

    @abstractmethod
    def setUp( self ):
        self.source = None

    def testRequestWait( self ):
        slicing = (slice(0,1),slice(10,20), slice(20,25), slice(0,1), slice(0,1))
        requested = self.source.request(slicing).wait()
        self.assertTrue(self.np.all(requested == self.raw[0:1,10:20,20:25,0:1,0:1]))

    def testRequestNotify( self ):
        slicing = (slice(0,1),slice(10,20), slice(20,25), slice(0,1), slice(0,1))
        request = self.source.request(slicing)
        
        def check(result, codon):
            self.assertTrue(self.np.all(result == self.raw[0:1,10:20,20:25,0:1,0:1]))
            self.assertEqual(codon, "unique")
        request.notify(check, codon="unique")

    def testSetDirty( self ):
        self.signal_emitted = False
        self.slicing = (slice(0,1),slice(10,20), slice(20,25), slice(0,1), slice(0,1))

        def slot( sl ):
            self.signal_emitted = True
            self.assertTrue( sl == self.slicing )

        self.source.isDirty.connect(slot)
        self.source.setDirty( self.slicing )
        self.source.isDirty.disconnect(slot)

        self.assertTrue( self.signal_emitted )

        del self.signal_emitted
        del self.slicing

class ArraySourceTest( ut.TestCase, GenericArraySourceTest ):
    def setUp( self ):
        import numpy as np
        self.np = np
        from scipy.misc import lena
        self.lena = lena()

        self.raw = np.zeros((1,512,512,1,1))
        self.raw[0,:,:,0,0] = self.lena
        self.source = ArraySource( self.raw )

try:
    import lazyflow
    has_lazyflow = True
except ImportError:
    has_lazyflow = False

if has_lazyflow:
    from lazyflow.graph import Graph
    from _testing import OpDataProvider

    class LazyflowSourceTest( ut.TestCase, GenericArraySourceTest ):
        def setUp( self ):
            import numpy as np
            self.np = np
            from scipy.misc import lena
            self.lena = lena()
            self.raw = np.zeros((1,512,512,1,1), dtype=np.uint8)
            self.raw[0,:,:,0,0] = self.lena

            g = Graph()
            op = OpDataProvider(g, self.raw)
            self.source = LazyflowSource(op, "Data")

if __name__ == '__main__':
    ut.main()

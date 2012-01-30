from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import RequestABC, SourceABC
import volumina
from volumina.slicingtools import is_pure_slicing, slicing2shape, is_bounded, index2slice
from volumina.config import cfg
import numpy as np

#*******************************************************************************
# A r r a y R e q u e s t                                                      *
#*******************************************************************************

class ArrayRequest( object ):
    def __init__( self, result ):
        self._result = result

    def wait( self ):
        return self._result
    
    def getResult(self):
        return self._result

    def cancel( self ):
        pass
        
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        callback(self._result, **kwargs)
assert issubclass(ArrayRequest, RequestABC)

#*******************************************************************************
# A r r a y S o u r c e                                                        *
#*******************************************************************************

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

assert issubclass(ArraySource, SourceABC)

#*******************************************************************************
# A r r a y S i n k S o u r c e                                                *
#*******************************************************************************

class ArraySinkSource( ArraySource ):
    def put( self, slicing, subarray, neutral = 0 ):
        '''Make an update of the wrapped arrays content.

        Elements with neutral value in the subarray are not written into the
        wrapped array, but the original values are kept.

        '''
        assert(len(slicing) == len(self._array.shape)), \
            "slicing into an array of shape=%r requested, but the slicing object is %r" % (slicing, self._array.shape)  
        self._array[slicing] = np.where(subarray!=neutral, subarray, self._array[slicing])
        pure = index2slice(slicing)
        self.setDirty(pure)

#*******************************************************************************
# R e l a b e l i n g A r r a y S o u r c e                                    * 
#*******************************************************************************

class RelabelingArraySource( QObject ):
    """Applies a relabeling to each request before passing it on
       Currently, it casts everything to uint8, so be careful."""
    isDirty = pyqtSignal( object )
    def __init__( self, array ):
        super(RelabelingArraySource, self).__init__()
        self._array = array
        self._relabeling = None
        
    def setRelabeling( self, relabeling ):
        self._relabeling = relabeling
        self.setDirty(5*(slice(None),))

    def request( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('ArraySource: slicing is not pure')
        assert(len(slicing) == len(self._array.shape)), \
            "slicing into an array of shape=%r requested, but the slicing object is %r" % (slicing, self._array.shape)
        a = self._array[slicing]
        if self._relabeling is not None:
            a = self._relabeling[a].astype(np.uint8)
        else:
            a = a.astype(np.uint8) #FIXME  
        return ArrayRequest(a)
        
    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
        
#*******************************************************************************
# L a z y f l o w R e q u e s t                                                *
#*******************************************************************************

class LazyflowRequest( object ):
    def __init__(self, lazyflow_request ):
        self._lazyflow_request = lazyflow_request

    def wait( self ):
        return self._lazyflow_request.wait()
        
    def getResult(self):
        return self._lazyflow_request.getResult()

    def adjustPriority(self,delta):
        self._lazyflow_request.adjustPriority(delta)
        
    def cancel( self ):
        self._lazyflow_request.cancel()

    def notify( self, callback, **kwargs ):
        self._lazyflow_request.notify( callback, **kwargs)
assert issubclass(LazyflowRequest, RequestABC)

#*******************************************************************************
# L a z y f l o w S o u r c e                                                  *
#*******************************************************************************

class LazyflowSource( QObject ):
    isDirty = pyqtSignal( object )

    def __init__( self, outslot, priority = 0 ):
        super(LazyflowSource, self).__init__()
        self._outslot = outslot
        self._priority = priority
        self._outslot.registerDirtyCallback(self.setDirty)

    def request( self, slicing ):
        if cfg.getboolean('pixelpipeline', 'verbose'):
            volumina.printLock.acquire()
            print "  LazyflowSource '%s' requests %s" % (self.objectName(), volumina.strSlicing(slicing))
            volumina.printLock.release()
        if not is_pure_slicing(slicing):
            raise Exception('LazyflowSource: slicing is not pure')
        if self._outslot.shape is not None:
            assert len(self._outslot.shape) == len(slicing), "shape mismatch: outslot of '%s' has shape = %r <--> slicing = %r" % (self._outslot.operator.name, self._outslot.shape, slicing)
            reqobj = self._outslot[slicing].allocate(priority = self._priority)        
        else:
            reqobj = ArrayRequest( np.zeros(slicing2shape(slicing), dtype=np.uint8 ) )
        return LazyflowRequest( reqobj )

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
        
assert issubclass(LazyflowSource, SourceABC)

class LazyflowSinkSource( LazyflowSource ):
    def __init__( self, operator, outslot, inslot, priority = 0 ):
        LazyflowSource.__init__(self, outslot)
        self._outputSlot = outslot
        self._inputSlot = inslot
        self._priority = priority
        self._outputSlot.registerDirtyCallback(self.setDirty)

    def request( self, slicing ):
        if cfg.getboolean('pixelpipeline', 'verbose'):
            volumina.printLock.acquire()
            print "  LazyflowSinkSource '%s' requests %s" % (self.objectName(), volumina.strSlicing(slicing))
            volumina.printLock.release()
        if not is_pure_slicing(slicing):
            raise Exception('LazyflowSinkSource: slicing is not pure')
        reqobj = self._outslot[slicing].allocate(priority = self._priority)        
        return LazyflowRequest( reqobj )

    def put( self, slicing, array ):
        self._inputSlot[slicing] = array
        pure = index2slice(slicing)
        
#*******************************************************************************
# C o n s t a n t R e q u e s t                                                *
#*******************************************************************************

class ConstantRequest( object ):
    def __init__( self, result ):
        self._result = result

    def wait( self ):
        return self._result
    
    def getResult(self):
        return self._result
    
    def cancel( self ):
        pass
        
    def adjustPriority(self, delta):
        pass        
        
    # callback( result = result, **kwargs )
    def notify( self, callback, **kwargs ):
        callback(self._result, **kwargs)
assert issubclass(ConstantRequest, RequestABC)

#*******************************************************************************
# C o n s t a n t S o u r c e                                                  *
#*******************************************************************************

class ConstantSource( QObject ):
    isDirty = pyqtSignal( object )

    def __init__( self, constant = 0, dtype = np.uint8 ):
        super(ConstantSource, self).__init__()
        self._constant = constant
        self._dtype = dtype

    def request( self, slicing ):
        assert is_pure_slicing(slicing)
        assert is_bounded(slicing)
        shape = slicing2shape(slicing)
        result = np.zeros( shape, dtype = self._dtype )
        result[:] = self._constant
        return ConstantRequest( result )

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
assert issubclass(ConstantSource, SourceABC)


#*******************************************************************************
#  T e s t                                                                     *
#*******************************************************************************

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

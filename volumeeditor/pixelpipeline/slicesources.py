import copy

from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import ArraySourceABC, RequestABC
import copy
import numpy as np

class SliceProjection( object ):
    @property
    def abscissa( self ):
        return self._abscissa
    @property
    def ordinate( self ):
        return self._ordinate
    @property
    def along( self ):
        return self._along
    @property
    def domainDim( self ):
        return self._dim

    def __init__( self, abscissa = 1, ordinate = 2, along = [0,3,4] ):
        assert hasattr(along, "__iter__")
        
        self._abscissa = abscissa
        self._ordinate = ordinate
        self._along = along
        self._dim = len(self.along) + 2

        # sanity checks
        axes_set = set(along)
        axes_set.add(abscissa)
        axes_set.add(ordinate)
        if len(axes_set) != self._dim:
            raise ValueError("duplicate axes")
        if axes_set != set(range(self._dim)):
            raise ValueError("axes not from range(0,dim)")
    
    def handednessSwitched( self ):
        if self.ordinate < self.abscissa:
            return True
        return False

    def domain( self, through, abscissa_range = slice(None, None), ordinate_range = slice(None,None) ):
        assert len(through) == len(self.along)
        slicing = range(self.domainDim)
        slicing[self.abscissa] = abscissa_range
        slicing[self.ordinate] = ordinate_range
        for i,a in enumerate(self.along):
            slicing[self.along[i]] = slice(through[i], through[i]+1)
        return tuple(slicing)

    def __call__( self, domainArray ):
        assert domainArray.ndim == self.domainDim
        slice = np.squeeze(domainArray)
        assert slice.ndim == 2, "dim %d != 2" % slice.ndim
        if self.handednessSwitched():
            slice = np.swapaxes(slice,0,1)
        return slice

projectionAlongTXC = SliceProjection( abscissa = 2, ordinate = 3, along = [0,1,4] )
projectionAlongTYC = SliceProjection( abscissa = 1, ordinate = 3, along = [0,2,4] )
projectionAlongTZC = SliceProjection( abscissa = 1, ordinate = 2, along = [0,3,4] )



class SliceRequest( object ):
    def __init__( self, domainArrayRequest, sliceProjection ):
        self._ar = domainArrayRequest
        self._sp = sliceProjection
        
    def wait( self ):
        return self._sp(self._ar.wait())

    def notify( self, callback, **kwargs ):
        self._arrayreq.notify(self._onNotify, package = (callback, kwargs))

    def _onNotify( self, result, package ):
        callback(self._sp(result), **kwargs)
assert issubclass(SliceRequest, RequestABC)

class SliceSource( QObject ):
    throughChanged = pyqtSignal( object )

    @property
    def through( self ):
        return self._through
    @through.setter
    def through( self, value ):
        self._through = value
        self.throughChanged.emit( self._through )

    def __init__(self, datasource, sliceProjection = projectionAlongTZC):
        assert isinstance(datasource, ArraySourceABC)
        super(SliceSource, self).__init__()

        self.sliceProjection = sliceProjection
        self._datasource = datasource
        self._through = len(sliceProjection.along) * [0]

    def request( self, slicing2D ):
        slicing = self.sliceProjection.domain(self.through, slicing2D[0], slicing2D[1])
        return SliceRequest(self._datasource.request(slicing), self.sliceProjection)
assert issubclass(SliceSource, ArraySourceABC)


class SpatialSliceSource( SliceSource ):
    def request(self, slicing2D):
        print "XXXXXXXXXXXXXXX [_along_axis=%s] slicing2D = %r" % (self._along_axis, slicing2D)
        return SliceSource.request(self, slicing2D)
    
    @property
    def index( self ):
        return self.through[1]
    @index.setter
    def index( self, value ):
        t = copy.copy(self.through)
        t[1] = value
        self.through = t

    @property
    def time( self ):
        return self.through[0]
    @time.setter
    def time( self, value ):
        t = copy.copy(self.through)
        t[0] = value
        self.through = t

    @property
    def channel( self ):
        return self._through[2]
    @channel.setter
    def channel( self, value ):
        t = copy.copy(self.through)
        t[2] = value
        self.through = t

    def __init__( self, datasource, along = 'z' ):
        projections = {'x': projectionAlongTXC, 'y': projectionAlongTYC, 'z': projectionAlongTZC}
        projection = projections[along]
        super(SpatialSliceSource, self).__init__( datasource, projection )
        self._through = [0,0,0]
assert issubclass(SpatialSliceSource, ArraySourceABC)






import unittest as ut
class SliceProjectionTest( ut.TestCase ):
    def testArgumentCheck( self ):
        SliceProjection(1,2,[0,3,4])
        SliceProjection(2,1,[3,0,4])
        self.assertRaises(ValueError, SliceProjection, 2,1,[3,0,7])
        self.assertRaises(ValueError, SliceProjection ,2,1,[3,1,4])
        self.assertRaises(ValueError, SliceProjection ,2,5,[3,1,4])

    def testDomain( self ):
        sp = SliceProjection(2,1,[3,0,4])
        unbounded = sp.domain([3,23,1])
        self.assertEqual(unbounded, (slice(23,24), slice(None), slice(None), slice(3,4), slice(1,2)))

        bounded = sp.domain([3,23,1], slice(5,9), slice(12,None))
        self.assertEqual(bounded, (slice(23,24), slice(12,None), slice(5,9), slice(3,4), slice(1,2)))

    def testSliceDomain( self ):
        sp = SliceProjection(2,1,[3,0,4])
        slicing = sp.domain([3,7,1], slice(1,3), slice(0,None))
        raw = np.random.randint(0,100,(10,3,3,128,3))
        domainArray = raw[slicing]
        sl = sp(domainArray)
        self.assertTrue(np.all(sl == raw[7,:,1:3,3,1].swapaxes(0,1)))



class SpatialSliceSourceTest( ut.TestCase ):
    def testRequest( self ):
        import numpy as np
        from datasources import ArraySource
        raw = np.random.randint(0,100,(10,3,3,128,3))
        a = ArraySource(raw)
        ss = SpatialSliceSource( a, 'z' )
        ss.time = 1
        ss.channel = 2
        ss.index = 127

        sl = ss.request((slice(None), slice(None))).wait()
        self.assertTrue(np.all(sl == raw[1,:,:,127,2]))

        sl_bounded = ss.request((slice(0, 3), slice(1, None))).wait()
        self.assertTrue(np.all(sl_bounded == raw[1,0:3,1:,127,2]))

if __name__ == '__main__':
    ut.main()

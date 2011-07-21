import copy

from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import ArraySourceABC, RequestABC
import numpy as np

def mkSlicer( abscissa = 1, ordinate = 2, along = [0,3,4] ):
    assert(hasattr(along, "__iter__"))
    def slicer( through = [0,0,0], abscissa_range = slice(None, None), ordinate_range = slice(None,None) ):
        slicing = range(len(through) + 2)
        slicing[abscissa] = abscissa_range
        slicing[ordinate] = ordinate_range
        for i,a in enumerate(along):
            slicing[a] = slice(through[i], through[i]+1)
        return slicing
    return slicer

XYSlicer5D = mkSlicer(1,2, [0,3,4])
XZSlicer5D = mkSlicer(1,3, [0,2,4])
YZSlicer5D = mkSlicer(2,3, [0,1,4])



class SliceRequest( object ):
    def __init__( self, array_request ):
        self._arrayreq = array_request
        
    def wait( self ):
        return np.squeeze(self._arrayreq.wait())

    def notify( self, callback, **kwargs ):
        self._arrayreq.notify(self._onNotify, package = (callback, kwargs))

    def _onNotify( self, result, package ):
        callback(np.squeeze(result), **kwargs)
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

    def __init__(self, datasource, slicer = XYSlicer5D):
        assert isinstance(datasource, ArraySourceABC)
        super(SliceSource, self).__init__()

        self._datasource = datasource
        self._through = []
        self._slicer = slicer

    def request( self, slicing2D ):
        slicing = self._slicer(self._through, slicing2D[0], slicing2D[1])
        return SliceRequest(self._datasource.request(slicing))
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
        print self._along_axis, value
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
        slicers = {'x': YZSlicer5D, 'y': XZSlicer5D, 'z': XYSlicer5D}
        slicer = slicers[along]
        super(SpatialSliceSource, self).__init__( datasource, slicer )
        self._through = [0,0,0]

        self.along = along
        self._along_axis = {'x': 1, 'y': 2, 'z': 3}[along]
assert issubclass(SpatialSliceSource, ArraySourceABC)



import unittest as ut
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

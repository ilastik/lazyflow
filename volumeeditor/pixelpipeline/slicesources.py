from PyQt4.QtCore import QObject, pyqtSignal
from asyncabcs import SourceABC, RequestABC
import copy
import numpy as np
from volumeeditor.slicingtools import SliceProjection, is_pure_slicing

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
    isDirty = pyqtSignal( object )

    @property
    def through( self ):
        return self._through
    @through.setter
    def through( self, value ):
        self._through = value
        self.setDirty((slice(None), slice(None)))

    def __init__(self, datasource, sliceProjection = projectionAlongTZC):
        assert isinstance(datasource, SourceABC)
        super(SliceSource, self).__init__()

        self.sliceProjection = sliceProjection
        self._datasource = datasource
        self._through = len(sliceProjection.along) * [0]

    def request( self, slicing2D ):
        slicing = self.sliceProjection.domain(self.through, slicing2D[0], slicing2D[1])
        return SliceRequest(self._datasource.request(slicing), self.sliceProjection)

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
assert issubclass(SliceSource, SourceABC)



class SyncedSliceSrcs( object ):
    isDirty = pyqtSignal( object )

    @property
    def through( self ):
        return self._through
    @through.setter
    def through( self, value ):
        self._through = value
        for src in self._srcs:
            src.through = value
        self.setDirty((slice(None), slice(None)))

    def __init__(self, slicesrcs = []):
        super(SyncedSliceSrcs, self).__init__()
        self._srcs = set(slicesrcs)
        self._through = None

    def __iter__( self ):
        return iter(self._srcs)

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )

    def add( self, sliceSrc ):
        assert issubclass( sliceSrc, SliceSource )
        self._srcs.add( sliceSrc )
        self.setDirty( (slice(None), slice(None)) ) 

    def remove( self, sliceSrc ):
        assert issubclass( sliceSrc, SliceSource )
        self._srcs.remove( sliceSrc )
        self.setDirty( slice(None) )         



class SpatialSliceSource( SliceSource ):
    @property
    def index( self ):
        return self.through[1]
    @index.setter
    def index( self, value ):
        t = copy.deepcopy(self.through)
        t[1] = value
        self.through = t

    @property
    def time( self ):
        return self.through[0]
    @time.setter
    def time( self, value ):
        t = copy.deepcopy(self.through)
        t[0] = value
        self.through = t

    @property
    def channel( self ):
        return self._through[2]
    @channel.setter
    def channel( self, value ):
        t = self._through
        t[2] = value
        self.through = t

    def __init__( self, datasource, along = 'z' ):
        projections = {'x': projectionAlongTXC, 'y': projectionAlongTYC, 'z': projectionAlongTZC}
        projection = projections[along]
        super(SpatialSliceSource, self).__init__( datasource, projection )
        self._through = [0,0,0]
assert issubclass(SpatialSliceSource, SourceABC)



class SyncedSpatialSliceSrcs( SyncedSliceSrcs ):
    @property
    def index( self ):
        return self.through[1]
    @index.setter
    def index( self, value ):
        t = self.through
        t[1] = value
        self.through = t

    @property
    def time( self ):
        return self.through[0]
    @time.setter
    def time( self, value ):
        t = self.through
        t[0] = value
        self.through = t

    @property
    def channel( self ):
        return self._through[2]
    @channel.setter
    def channel( self, value ):
        t = self._through
        t[2] = value
        self.through = t






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

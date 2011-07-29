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
        assert isinstance(datasource, SourceABC) , 'wrong type: %s' % str(type(datasource)) 
        super(SliceSource, self).__init__()

        self.sliceProjection = sliceProjection
        self._datasource = datasource
        self._through = len(sliceProjection.along) * [0]

    def setThrough( self, index, value ):
        assert index < len(self.through)
        through = self.through
        through[index] = value
        self.through = through

    def request( self, slicing2D ):
        slicing = self.sliceProjection.domain(self.through, slicing2D[0], slicing2D[1])
        return SliceRequest(self._datasource.request(slicing), self.sliceProjection)

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )
assert issubclass(SliceSource, SourceABC)



class SyncedSliceSources( QObject ):
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
        super(SyncedSliceSources, self).__init__()
        self._srcs = set(slicesrcs)
        self._through = None

    def __iter__( self ):
        return iter(self._srcs)

    def setThrough( self, index, value ):
        assert index < len(self.through)
        through = self.through
        through[index] = value
        self.through = through

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        self.isDirty.emit( slicing )

    def add( self, sliceSrc ):
        assert isinstance( sliceSrc, SliceSource ), 'wrong type: %s' % str(type(sliceSrc))
        self._srcs.add( sliceSrc )
        self.setDirty( (slice(None), slice(None)) ) 

    def remove( self, sliceSrc ):
        assert issubclass( sliceSrc, SliceSource )
        self._srcs.remove( sliceSrc )
        self.setDirty( slice(None) )         






import unittest as ut
class SliceSourceTest( ut.TestCase ):
    def testRequest( self ):
        import numpy as np
        from datasources import ArraySource
        raw = np.random.randint(0,100,(10,3,3,128,3))
        a = ArraySource(raw)
        ss = SliceSource( a, projectionAlongTZC )
        ss.setThrough(0, 1)
        ss.setThrough(2, 2)
        ss.setThrough(1, 127)

        sl = ss.request((slice(None), slice(None))).wait()
        self.assertTrue(np.all(sl == raw[1,:,:,127,2]))

        sl_bounded = ss.request((slice(0, 3), slice(1, None))).wait()
        self.assertTrue(np.all(sl_bounded == raw[1,0:3,1:,127,2]))

if __name__ == '__main__':
    ut.main()

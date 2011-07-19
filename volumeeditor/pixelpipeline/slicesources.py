from PyQt4.QtCore import QObject, pyqtSignal

def mkSlicer( abscissa = 1, ordinate = 2, along = [0,3,4] ):
    assert(hasattr(along, "__iter__"))
    def slicer( through = [0,0,0], abscissa_range = slice(None, None), ordinate_range = slice(None,None) ):
        slicing = range(len(through) + 2)
        slicing[abscissa] = abscissa_range
        slicing[ordinate] = ordinate_range
        for i,a in enumerate(along):
            slicing[a] = through[i]
        return slicing
    return slicer

XYSlicer5D = mkSlicer(1,2, [0,3,4])
XZSlicer5D = mkSlicer(1,3, [0,2,4])
YZSlicer5D = mkSlicer(2,3, [0,1,4])



class Slice( QObject ):
    throughChanged = pyqtSignal()
    slicingChanged = pyqtSignal()

    @property
    def through( self ):
        return self._through
    @through.setter
    def through( self ):
        self._through

    def __init__(self, datasource, slicer = XYSlicer5D):
        self._datasource = datasource
        self._through = []
        self._slicer = slicer

    def request( self, slicing ):
        self._slicer(self._through, slicing[0], slicing[1])



class SliceOf5D( QObject ):
    changed = pyqtSignal()

    @property
    def through( self ):
        return self._coords[1]
    @through.setter
    def through( self, value ):
        self._coords[1] = value
        self.request()
    '''
    @property
    def time( self ):
        return self._time
    @time.setter
    def time( self, value ):
        self._time = value
        self.changed.emit()

    '''
    @property
    def channel( self ):
        return self._coords[2]
    @channel.setter
    def channel( self, value ):
        self._coords[2] = value
        self.request()
    
    def __init__( self, datasource, along = 'z' ):
        super(SpatialSliceSource5D, self).__init__()

        self._slice = None
        self._coords = [0,0,0] # time, through, channel
        self._ranges = ((None, None), (None, None))

        #self._time = 0
        #self._channel = 0
        self._datasource = datasource
        #self._through = 0

        self._datasource.changed.connect(self._do)

        # create slicer
        axis = {'x': 1, 'y': 2, 'z': 3}
        _along = axis[along]
        axes = [1,2,3]
        axes.remove(_along)
        self._slicer = mkSlicer(axes[0],axes[1],[0,_along,4])

    def request( self , ranges = ((None, None), (None, None)) ):
        self._datasource.request((slice(None), slice(None), slice(None), slice(None), slice(None)) )

    def _do( self, slicing, slicedarray ):
        self._slice = self._slicer(slicedarray, self._coords, self._ranges)
        self.changed.emit()



import unittest as ut
class SpatialSliceSource5DTest( ut.TestCase ):
    def testRequest( self ):
        import numpy as np
        a = np.random.randint(0,100,(10,3,3,128,3))
        ss = SpatialSliceSource5D( a, 'z' )
        ss.time = 1
        ss.channel = 2
        ss.through = 127

        sl = ss.request()
        self.assertTrue(np.all(sl == a[1,:,:,127,2]))

        sl_bounded = ss.request(((0, 3), (1, None)))
        self.assertTrue(np.all(sl_bounded == a[1,0:3,1:,127,2]))

if __name__ == '__main__':
    ut.main()

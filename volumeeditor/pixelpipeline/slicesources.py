from PyQt4.QtCore import QObject, pyqtSignal

def mkSlicer( abscissa = 1, ordinate = 2, along = [0,3,4] ):
    assert(hasattr(along, "__iter__"))
    def slicer( array, through = [0,0,0], ranges = ((None, None), (None,None)) ):
        slicing = range(len(through) + 2)
        slicing[abscissa] = slice(ranges[0][0], ranges[0][1])
        slicing[ordinate] = slice(ranges[1][0], ranges[1][1])
        for i,a in enumerate(along):
            slicing[a] = through[i]
        return array[slicing]
    return slicer



class SpatialSliceSource5D( QObject ):
    changed = pyqtSignal()

    @property
    def through( self ):
        return self._through
    @through.setter
    def through( self, value ):
        self._through = value
        self.changed.emit()

    @property
    def time( self ):
        return self._time
    @time.setter
    def time( self, value ):
        self._time = value
        self.changed.emit()

    @property
    def channel( self ):
        return self._channel
    @channel.setter
    def channel( self, value ):
        self._channel = value
        self.changed.emit()

    def __init__( self, array, along = 'z' ):
        super(SpatialSliceSource5D, self).__init__()
        self._time = 0
        self._channel = 0
        self._array = array
        self._through = 0

        # create slicer
        axis = {'x': 1, 'y': 2, 'z': 3}
        _along = axis[along]
        axes = [1,2,3]
        axes.remove(_along)
        self._slicer = mkSlicer(axes[0],axes[1],[0,_along,4])

    def request( self , ranges = ((None, None), (None, None)) ):
        return self._slicer(self._array, [self.time, self.through, self.channel], ranges)



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

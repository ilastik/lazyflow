import numpy as np
from PyQt4.QtCore import QRect

'''Provide tools to work with collections of slice instances.

A n-dimensional slicing is a sequence of n slice objects, for example:
slicing = [slice(10,23), slice(None), slice(14,None)]

The sequence has to support __iter__, __setitem__, and __getitem__,
as the common Python sequence types tuple and list do.

Additionally, a 1-dimensional slicing may consist of a single slice instance
not wrapped in a sequence.

'''
        
class Sl( object ):
    '''Helper to create slicings using nice subsprict syntax.

    sl = Sl()
    slicing = sl[1:2,:]

    '''
    def __getitem__( self, slicing ):
        return slicing
sl = Sl()

def box( sl, seq=tuple ):
    '''Wraps a single slice with a sequence.

    No effect on any other object.

   '''
    if isinstance(sl, slice):
        return seq((sl,))
    else:
        return sl

def unbox( slicing, axis=0 ):
    '''Extracts a slice object from a sequence of slices.

    No effect in any other case.

    '''
    if hasattr( slicing, '__iter__' ):
        if len(slicing) > axis and isinstance(slicing[axis], slice):
            return slicing[axis]
    return slicing

def is_bounded( slicing ):
    '''For all dimensions: stop value of slice is not None '''
    slicing = box(slicing)
    return all((sl.stop != None for sl in slicing))

def is_pure_slicing( slicing ):
    '''Test if slicing is a single slice instance or sequence of instances.

    Impure slicings may additionally contain integer indices, 
    ellipses, booleans, or newaxis.
    '''
    slicing = box(slicing)
    if not hasattr(slicing, '__iter__'):
        return False
    for thing in slicing:
        if not isinstance(thing, slice):
            return False
    return True

def slicing2rect( slicing, width_axis=1, height_axis = 0 ):
    x = slicing[width_axis].start
    y = slicing[height_axis].start
    width = slicing[width_axis].stop - slicing[width_axis].start
    height = slicing[height_axis].stop - slicing[height_axis].start
    return QRect(x, y, width, height)

def rect2slicing( qrect, seq=tuple ):
    return seq((slice(qrect.y(), qrect.y()+qrect.height()), slice(qrect.x(), qrect.x()+qrect.width())))

def slicing2shape( slicing ):
    assert is_bounded( slicing )
    slicing = box(slicing)
    shape = []
    for sl in slicing:
        shape.append(sl.stop - sl.start)
    return tuple(shape)

def intersection( lhs, rhs ):
    '''Calculate intersection between two slicings of same dimensions.

    Intersection is represented as a slicing, too.
    Returns None if the intersection is empty.

    '''
    assert len(lhs) == len(rhs)
    assert is_pure_slicing(lhs) and is_pure_slicing(rhs)
    dim = len(lhs)
    inter = [None] * dim 
    for d in xrange(dim):
        start = max(lhs[d].start, rhs[d].start)
        stop = min(lhs[d].stop, rhs[d].stop)
        if( (stop - start) <= 0):
            return None
        inter[d] = slice(start, stop)
    return tuple(inter)





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






import unittest as ut
class SlTest( ut.TestCase ):
    def runTest( self ):
        self.assertEqual(sl[1,:34,:], (1, slice(34), slice(None)))

class toolsTest( ut.TestCase ):
    def testIntersection( self ):
        i = intersection(sl[5:8, 3:7, 2:9],sl[0:50, 0:50,4:5])
        self.assertEqual(i, sl[5:8, 3:7, 4:5])
        ni = intersection(sl[5:8, 3:7, 2:9],sl[0:50, 0:50,9:10])
        self.assertEqual(ni, None)

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

if __name__ == '__main__':
    ut.main()

from PyQt4.QtCore import QRect

'''Provide tools to work with collections of slice instances.

A n-dimensional slicing is a sequence of n slice objects, for example:
slicing = [slice(10,23), slice(None), slice(14,None)]

The sequence has to support __iter__, __setitem__, and __getitem__,
as the common Python sequence types tuple and list do.

Additionally, a 1-dimensional slicing may consist of a single slice instance
not wrapped in a sequence.

'''

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

def slicing2rect( slicing, width_axis=1, height_axis = 0 ):
    x = slicing[width_axis].start
    y = slicing[height_axis].start
    width = slicing[width_axis].stop - slicing[width_axis].start
    height = slicing[height_axis].stop - slicing[height_axis].start
    return QRect(x, y, width, height)

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

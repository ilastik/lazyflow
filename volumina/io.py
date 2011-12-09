'''Input and output from and to other libraries resp. formats.

Volumine works with 5d array-like objects assuming the coordinate
system (time, x, y, z, channel). This module provides methods to convert other
data types to this expected format.
'''
import os
import os.path as path
import numpy as np
from volumina.slicingtools import sl, slicing2shape

###
### lazyflow input
###
_has_lazyflow = True
try:
    from lazyflow.graph import Operator, InputSlot, OutputSlot
except ImportError:
    _has_lazyflow = False

if _has_lazyflow:
    class Op5ifyer(Operator):
        name = "5Difyer"
        inputSlots = [InputSlot("Input", stype='ndarray')]
        outputSlots = [OutputSlot("Output")]
        def notifyConnectAll(self):
            shape = self.inputs["Input"].shape
            assert len(shape) == 3
            outShape = (1,) + shape + (1,)
            self.outputs["Output"]._shape = outShape
            self.outputs["Output"]._dtype = self.inputs["Input"].dtype
            self.outputs["Output"]._axistags = self.inputs["Input"].axistags

        def getOutSlot(self, slot, key, resultArea):
            assert key[0] == slice(0,1,None)
            assert key[-1] == slice(0,1,None)
            req = self.inputs["Input"][key[1:-1]].writeInto(resultArea[0,:,:,:,0])
            return req.wait()

        def notifyDirty(self,slot,key):
            self.outputs["Output"].setDirty(key)



class Array5d( object ):
    '''Embed a array with dim = 3 into the volumina coordinate system.'''
    def __init__( self, array, dtype=np.uint8):
        assert(len(array.shape) == 3)
        self.a = array
        self.dtype=dtype
        
    def __getitem__( self, slicing ):
        sl3d = (slicing[1], slicing[2], slicing[3])
        ret = np.zeros(slicing2shape(slicing), dtype=self.dtype)
        ret[0,:,:,:,0] = self.a[tuple(sl3d)]
        return ret
    @property
    def shape( self ):
        return (1,) + self.a.shape + (1,)

    def astype( self, dtype):
        return Array5d( self.a, dtype )



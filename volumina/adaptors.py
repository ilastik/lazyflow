'''Input and output from and to other libraries resp. formats.

Volumine works with 5d array-like objects assuming the coordinate
system (time, x, y, z, channel). This module provides methods to convert other
data types to this expected format.
'''
import os
import os.path as path
import numpy as np
from volumina.slicingtools import sl, slicing2shape
import vigra

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
        inputSlots = [InputSlot("Input")]
        outputSlots = [OutputSlot("Output")]
        def notifyConnectAll(self):
            inputAxistags = self.inputs["Input"].axistags
            inputShape = self.inputs["Input"].shape
            assert len(inputShape) == len(inputAxistags), "Op5ifyer: my input coming from operator '%s' has inconsistent shape and axistags information" % (self.inputs["Input"].partner.operator.name)
            outShape = 5*[1,]
            voluminaOrder = ['t', 'x', 'y', 'z', 'c']
            inputOrder = []
            order = []
            self.slicing = 5*[0]
            for i, channel in enumerate(inputAxistags):
                assert channel.key in voluminaOrder
                order.append(voluminaOrder.index(channel.key))
                outShape[ voluminaOrder.index(channel.key) ] = inputShape[i] 
                self.slicing[ voluminaOrder.index(channel.key) ] = slice(None,None)
                inputOrder.append(channel.key)
            assert order == sorted(order)
            self.keyStart = voluminaOrder.index(inputOrder[0])
            self.keyStop = voluminaOrder.index(inputOrder[-1])

            self.ndim = len(inputShape)
            self.outputs["Output"]._shape = outShape
            self.outputs["Output"]._dtype = self.inputs["Input"].dtype
          
            t = vigra.AxisTags()
            t.insert(0, vigra.AxisInfo('t', vigra.AxisType.Time))
            t.insert(1, vigra.AxisInfo('x', vigra.AxisType.Space))
            t.insert(2, vigra.AxisInfo('y', vigra.AxisType.Space))
            t.insert(3, vigra.AxisInfo('z', vigra.AxisType.Space))
            t.insert(4, vigra.AxisInfo('c', vigra.AxisType.Channels))

            self.outputs["Output"]._axistags = t 

        def execute(self, slot, key, resultArea):
            key = key.toSlice()
            assert resultArea.ndim == 5
            inputSlicing = key[slice(self.keyStart, self.keyStop+1)]
            assert len(inputSlicing) == len(self.inputs["Input"]._shape), "inputSlicing = %r, input shape = %r" % (inputSlicing, self.inputs["Input"]._shape)
            req = self.inputs["Input"][inputSlicing].writeInto(resultArea[self.slicing])
            req.wait()
            return resultArea 

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



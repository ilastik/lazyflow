from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow import operators

import numpy as np
import time

class Op5ifyer(Operator):
    name = "5Difyer"

    inputSlots = [InputSlot("Input", stype="ndarray")]
    outputSlots = [OutputSlot("Output", stype="ndarray")]

    def notifyConnectAll(self):
        shape = self.inputs["Input"].shape
        assert len(shape) == 3
        outShape = (1,) + shape[0:2] + (1,) + (shape[2],)
        self.outputs["Output"]._shape = outShape
        self.outputs["Output"]._dtype = self.inputs["Input"].dtype
        self.outputs["Output"]._axistags = self.inputs["Input"].axistags
        

    def getOutSlot(self, slot, key, resultArea):
        assert key[0] == slice(0,1,None)
        assert key[-2] == slice(0,1,None)
        req = self.inputs["Input"][key[1:-2] + (key[-1],)].writeInto(resultArea[0,:,:,0,:])
        req.wait()

class OpDelay(operators.OpArrayPiper):
    def __init__( self, g, delay_factor = 0.000001 ):
        super(OpDelay, self).__init__(g)
        self._delay_factor = delay_factor

    def getOutSlot(self, slot, key, resultArea):
        req = self.inputs["Input"][key].writeInto(resultArea)
        req.wait()
        t = self._delay_factor*resultArea.nbytes
        print "Delay: " + str(t) + " secs."
        time.sleep(t)    

class OpDataProvider5D(Operator):
    name = "Data Provider 5D"
    category = "Input"
    
    inputSlots = []
    outputSlots = [OutputSlot("Data5D")]
    
    def __init__(self, g, fn):
        Operator.__init__(self,g)
        self._data = np.load(fn)
        oslot = self.outputs["Data5D"]
        oslot._shape = self._data.shape
        oslot._dtype = self._data.dtype
    
    def getOutSlot(self, slot, key, result):
        result[:] = self._data[key]

import sys
fn = sys.argv[1]

g = Graph()

op1 = OpDataProvider5D(g, fn)
op2 = OpDelay(g, 0.0000001)

op2.inputs["Input"].connect(op1.outputs["Data5D"])

result = op2.outputs["Output"][:].allocate().wait()
print "obtained data with shape " + str(result.shape)

g.finalize()

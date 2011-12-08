from lazyflow.graph import Operator, InputSlot, OutputSlot

class Op5ifyer(Operator):
    name = "5Difyer"
    inputSlots = [InputSlot("Input", stype="ndarray")]
    outputSlots = [OutputSlot("Output", stype="ndarray")]
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
        req.wait()


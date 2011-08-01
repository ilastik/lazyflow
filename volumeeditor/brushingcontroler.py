from PyQt4.QtCore import QObject

import qimage2ndarray

class CrosshairControler(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._brushingModel = brushingModel
        self._brushingModel.brushSizeChanged.connect(self._setBrushSize)
        self._brushingModel.brushColorChanged.connect(self._setBrushColor)
    
    def _setBrushSize(self):
        pass
    
    def _setBrushColor(self):
        pass
        
class BrushingControler(QObject):
    def __init__(self, brushingModel, dataSink):
        QObject.__init__(self, parent=None)
        self._dataSink = dataSink
        self._brushingModel = brushingModel
        
        self._brushingModel.brushStrokeAvailable.connect(self._writeIntoSink)
        
    def _writeIntoSink(self, brushStrokeOffset, brushStrokeImage):
        print "BrushingControler._writeIntoSink(%r, %r)" % (brushStrokeOffset, brushStrokeImage)
        import time
        t = time.time()
        
        brushStrokeImage.save("%d.png" % t)
        
        #this code shows how to convert the QImage back to a numpy array
        ndarr = qimage2ndarray.rgb_view(brushStrokeImage)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        import vigra
        vigra.impex.writeImage(labels, "%d_vigra.png" % t)
        
        #TODO:
        #ndarray = brushStroke.toNDarray()
        #self._dataSink.put([offset+shape(ndarray)]) = ndarray
        
class BrushingInterpreter(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._imageViews = imageViews
        self._brushingModel = brushingModel
        for i in range(3):
            self._imageViews[i].beginDraw.connect(self._brushingModel.beginDrawing)
            self._imageViews[i].endDraw.connect(self._brushingModel.endDrawing)
            self._imageViews[i].drawing.connect(self._brushingModel.moveTo)
    
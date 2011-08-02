from PyQt4.QtCore import QObject

from volumeeditor.positionModel import PositionModel

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
    def __init__(self, brushingModel, positionModel, dataSink):
        QObject.__init__(self, parent=None)
        self._dataSink = dataSink
        
        self._brushingModel = brushingModel
        self._brushingModel.brushStrokeAvailable.connect(self._writeIntoSink)
        self._positionModel = positionModel
        
    def _writeIntoSink(self, brushStrokeOffset, brushStrokeImage):
        #print "BrushingControler._writeIntoSink(%r, %r)" % (brushStrokeOffset, brushStrokeImage)
        ndarr = qimage2ndarray.rgb_view(brushStrokeImage)
        labels = ndarr[:,:,0]
        
        activeView = self._positionModel.activeView
        slicingPos = self._positionModel.slicingPos
        t, c       = self._positionModel.time, self._positionModel.channel
        
        slicing = [slice(brushStrokeOffset.y(), brushStrokeOffset.y()+brushStrokeImage.height()), \
                     slice(brushStrokeOffset.x(), brushStrokeOffset.x()+brushStrokeImage.width())]
        slicing.insert(activeView, slicingPos[activeView])
        
        slicing = (t,) + tuple(slicing) + (c,)
        print "_writeIntoSink", slicing, labels.shape
        
        self._dataSink.put(slicing, labels)
        
class BrushingInterpreter(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._imageViews = imageViews
        self._brushingModel = brushingModel
        for i in range(3):
            self._imageViews[i].beginDraw.connect(self._brushingModel.beginDrawing)
            self._imageViews[i].endDraw.connect(self._brushingModel.endDrawing)
            self._imageViews[i].drawing.connect(self._brushingModel.moveTo)
    

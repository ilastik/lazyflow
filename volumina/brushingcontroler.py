from PyQt4.QtCore import QObject

#*******************************************************************************
# C r o s s h a i r C o n t r o l e r                                          *
#*******************************************************************************

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
        
#*******************************************************************************
# B r u s h i n g C o n t r o l e r                                            *
#*******************************************************************************

class BrushingControler(QObject):
    def __init__(self, brushingModel, positionModel, dataSink):
        QObject.__init__(self, parent=None)
        self._dataSink = dataSink
        
        self._brushingModel = brushingModel
        self._brushingModel.brushStrokeAvailable.connect(self._writeIntoSink)
        self._positionModel = positionModel
        
    def _writeIntoSink(self, brushStrokeOffset, labels):
        activeView = self._positionModel.activeView
        slicingPos = self._positionModel.slicingPos
        t, c       = self._positionModel.time, self._positionModel.channel
        
        slicing = [slice(brushStrokeOffset.x(), brushStrokeOffset.x()+labels.shape[0]), \
                   slice(brushStrokeOffset.y(), brushStrokeOffset.y()+labels.shape[1])]
        slicing.insert(activeView, slicingPos[activeView])
        slicing = (t,) + tuple(slicing) + (c,)
        
        #make the labels 5d for correct graph compatibility
        newshape = list(labels.shape)
        newshape.insert(activeView, 1)
        newshape.insert(0, 1)
        newshape.append(1)
        
        #newlabels = numpy.zeros
        
        self._dataSink.put(slicing, labels.reshape(tuple(newshape)))
        
#*******************************************************************************
# B r u s h i n g I n t e r p r e t e r                                        *
#*******************************************************************************

class BrushingInterpreter(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._imageViews = imageViews
        self._brushingModel = brushingModel
        for i in range(3):
            self._imageViews[i].beginDraw.connect(self._brushingModel.beginDrawing)
            self._imageViews[i].endDraw.connect(self._brushingModel.endDrawing)
            self._imageViews[i].drawing.connect(self._brushingModel.moveTo)
            self._imageViews[i].erasingToggled.connect(self._brushingModel.toggleErase)
    

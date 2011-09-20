from PyQt4.QtCore import QObject, QEvent, QPointF, Qt
from PyQt4.QtGui import QPainter, QPen, QApplication

from eventswitch import InterpreterABC

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
# B r u s h i n g I n t e r p r e t e r                                        *
#*******************************************************************************

class BrushingInterpreter( QObject ):
    def __init__( self, navigationInterpreter, navigationControler ):
        QObject.__init__( self )
        self._navCtrl = navigationControler
        self._navIntr = navigationInterpreter 

    def start( self ):
        self._navCtrl.drawingEnabled = True

    def finalize( self ):
        if self._navCtrl._isDrawing:
            for imageview in self._navCtrl._views:
                self._navCtrl.endDrawing(imageview, imageview.mousePos)
        self._navCtrl.drawingEnabled = False

    def eventFilter( self, watched, event ):
        etype = event.type()
        if etype == QEvent.MouseMove:
            self.onMouseMoveEvent( watched, event )
            return True
        elif etype == QEvent.Wheel:
            self.onWheelEvent( watched, event )
            return True
        elif etype == QEvent.MouseButtonPress:
            self.onMousePressEvent( watched, event )
            return True
        elif etype == QEvent.MouseButtonRelease:
            self.onMouseReleaseEvent( watched, event )
            return True
        elif etype == QEvent.MouseButtonDblClick:
            self.onMouseDoubleClickEvent( watched, event )
            return True
        else:
            return False


    def onMouseMoveEvent( self, imageview, event ):
        if imageview._dragMode == True:
            #the mouse was moved because the user wants to change
            #the viewport
            imageview._deltaPan = QPointF(event.pos() - imageview._lastPanPoint)
            imageview._panning()
            imageview._lastPanPoint = event.pos()
            return
        if imageview.ticker.isActive():
            #the view is still scrolling
            #do nothing until it comes to a complete stop
            return
        
        imageview.mousePos = mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        oldX, oldY = imageview.x, imageview.y
        x = imageview.x = mousePos.x()
        y = imageview.y = mousePos.y()
        self._navCtrl.positionCursor( x, y, self._navCtrl._views.index(imageview))

        if self._navCtrl._isDrawing:
            o   = imageview.scene().data2scene.map(QPointF(oldX,oldY))
            n   = imageview.scene().data2scene.map(QPointF(x,y))
            pen = QPen(self._navCtrl._brushingModel.drawColor, self._navCtrl._brushingModel.brushSize)
            imageview.scene().drawLine(o, n, pen)

            self._navCtrl._brushingModel.moveTo(mousePos)

    def onWheelEvent( self, imageview, event ):
        k_alt = (event.modifiers() == Qt.AltModifier)
        k_ctrl = (event.modifiers() == Qt.ControlModifier)

        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))

        sceneMousePos = imageview.mapToScene(event.pos())
        grviewCenter  = imageview.mapToScene(imageview.viewport().rect().center())

        if event.delta() > 0:
            if k_alt:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    imageview._isDrawing = True
                self._navCtrl.changeSliceRelative(10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 1.1
                imageview.doScale(scaleFactor)
            else:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(1, self._navCtrl._views.index(imageview))
        else:
            if k_alt:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(-10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 0.9
                imageview.doScale(scaleFactor)
            else:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(-1, self._navCtrl._views.index(imageview))
        if k_ctrl:
            mousePosAfterScale = imageview.mapToScene(event.pos())
            offset = sceneMousePos - mousePosAfterScale
            newGrviewCenter = grviewCenter + offset
            imageview.centerOn(newGrviewCenter)
            self.onMouseMoveEvent( imageview, event)

    def onMousePressEvent( self, imageview, event ):
        if event.button() == Qt.MidButton:
            imageview.setCursor(QCursor(Qt.SizeAllCursor))
            imageview._lastPanPoint = event.pos()
            imageview._crossHairCursor.setVisible(False)
            imageview._dragMode = True
            if imageview.ticker.isActive():
                imageview._deltaPan = QPointF(0, 0)

        if event.buttons() == Qt.RightButton:
            #make sure that we have the cursor at the correct position
            #before we call the context menu
            self.onMouseMoveEvent( imageview, event)
            imageview.customContextMenuRequested.emit(event.pos())
            return

        if not self._navCtrl.drawingEnabled:
            return
        
        if event.buttons() == Qt.LeftButton:
            #don't draw if flicker the view
            if imageview.ticker.isActive():
                return
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self._navCtrl._brushingModel.setErasing()
                self._navCtrl._tempErase = True
            imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
            self._navCtrl.beginDrawing(imageview, imageview.mousePos)

    def onMouseReleaseEvent( self, imageview, event ):
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        
        if event.button() == Qt.MidButton:
            imageview.setCursor(QCursor())
            releasePoint = event.pos()
            imageview._lastPanPoint = releasePoint
            imageview._dragMode = False
            imageview.ticker.start(20)
        if self._navCtrl._isDrawing:
            self._navCtrl.endDrawing(imageview, imageview.mousePos)
        if self._navCtrl._tempErase:
            self._navCtrl._brushingModel.disableErasing()
            self._navCtrl._tempErase = False

    def onMouseDoubleClickEvent( self, imageview, event ):
        dataMousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        imageview.mousePos = dataMousePos # FIXME: remove, when guaranteed, that no longer needed inside imageview
        self._navCtrl.positionSlice(dataMousePos.x(), dataMousePos.y(), self._navCtrl._views.index(imageview))
assert issubclass(BrushingInterpreter, InterpreterABC)
        
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

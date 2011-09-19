from PyQt4.QtCore import QObject, QTimer, QEvent, Qt, QPointF, pyqtSignal
from PyQt4.QtGui  import QColor, QCursor, QMouseEvent, QApplication, QPainter, QPen

import  copy
from functools import partial

from imageView2D import ImageView2D
from imageScene2D import ImageScene2D
from eventswitch import InterpreterABC

def posView2D(pos3d, axis):
    """convert from a 3D position to a 2D position on the slicing plane
       perpendicular to axis"""
    pos2d = copy.deepcopy(pos3d)
    del pos2d[axis]
    return pos2d

#*******************************************************************************
# N a v i g a t i o n I n t e r p r e t e r                                    *
#*******************************************************************************

class NavigationInterpreter(QObject):
    """
    Provides slots to listens to mouse/keyboard events from multiple
    slice views and interprets them as actions upon a N-D volume
    (whereas the individual ImageView2D/ImageScene2D know nothing about the
    data they display).

    """
    def __init__(self, navigationcontroler):
        """
        Constructs an interpreter which will update the
        PositionModel model.
        
        The user of this class needs to make the appropriate connections
        from the ImageView2D to the methods of this class from the outside 
        himself.
        """
        QObject.__init__(self)
        self._navCtrl = navigationcontroler

    def start( self ):
        pass

    def finalize( self ):
        pass

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

    def onWheelEvent( self, imageview, event ):
        k_alt = (event.modifiers() == Qt.AltModifier)
        k_ctrl = (event.modifiers() == Qt.ControlModifier)

        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))

        sceneMousePos = imageview.mapToScene(event.pos())
        grviewCenter  = imageview.mapToScene(imageview.viewport().rect().center())

        if event.delta() > 0:
            if k_alt:
                self._navCtrl.changeSliceRelative(10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 1.1
                imageview.doScale(scaleFactor)
            else:
                self._navCtrl.changeSliceRelative(1, self._navCtrl._views.index(imageview))
        else:
            if k_alt:
                self._navCtrl.changeSliceRelative(-10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 0.9
                imageview.doScale(scaleFactor)
            else:
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

    def onMouseReleaseEvent( self, imageview, event ):
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        
        if event.button() == Qt.MidButton:
            imageview.setCursor(QCursor())
            releasePoint = event.pos()
            imageview._lastPanPoint = releasePoint
            imageview._dragMode = False
            imageview.ticker.start(20)

    def onMouseDoubleClickEvent( self, imageview, event ):
        dataMousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        imageview.mousePos = dataMousePos # FIXME: remove, when guaranteed, that no longer needed inside imageview
        self._navCtrl.positionSlice(dataMousePos.x(), dataMousePos.y(), self._navCtrl._views.index(imageview))
assert issubclass(NavigationInterpreter, InterpreterABC)    

#*******************************************************************************
# N a v i g a t i o n C o n t r o l e r                                        *
#*******************************************************************************

class NavigationControler(QObject):
    """
    Controler for navigating through the volume.
    
    The NavigationContrler object listens to changes
    in a given PositionModel and updates three slice
    views (representing the spatial X, Y and Z slicings)
    accordingly.
    """
    # all the following signals refer to data coordinates
    drawing            = pyqtSignal(QPointF)
    beginDraw          = pyqtSignal(QPointF, object)
    endDraw            = pyqtSignal(QPointF)
    
    erasingToggled     = pyqtSignal(bool)            
    
    @property
    def axisColors( self ):
        return self._axisColors
    @axisColors.setter
    def axisColors( self, colors ):
        self._axisColors = colors
        self._views[0]._sliceIntersectionMarker.setColor(self.axisColors[1], self.axisColors[2])
        self._views[1]._sliceIntersectionMarker.setColor(self.axisColors[0], self.axisColors[2])
        self._views[2]._sliceIntersectionMarker.setColor(self.axisColors[0], self.axisColors[1])
        for axis, v in enumerate(self._views):
            #FIXME: Bad dependency here on hud to be available!
            if v.hud: v.hud.bgColor = self.axisColors[axis]
        
    @property
    def indicateSliceIntersection(self):
        return self._indicateSliceIntersection
    @indicateSliceIntersection.setter
    def indicateSliceIntersection(self, show):
        self._indicateSliceIntersection = show
        for v in self._views:
            v._sliceIntersectionMarker.setVisibility(show)
        
    def __init__(self, imageView2Ds, sliceSources, positionModel, brushingModel, time = 0, channel = 0, view3d=None):
        QObject.__init__(self)
        assert len(imageView2Ds) == 3

        # init fields
        self._views = imageView2Ds
        self._sliceSources = sliceSources
        self._model = positionModel
        self._beginStackIndex = 0
        self._endStackIndex   = 1
        self._view3d = view3d

        self.drawingEnabled = False
        self._isDrawing = False
        self._tempErase = False
        self._brushingModel = brushingModel

        self.axisColors = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]
    
    def moveCrosshair(self, newPos, oldPos):
        self._updateCrossHairCursor()

    def positionSlice(self, x, y, axis):
        newPos = copy.copy(self._model.slicingPos)
        i,j = posView2D([0,1,2], axis)
        newPos[i] = x
        newPos[j] = y
        if newPos == self._model.slicingPos:
            return
        if not self._positionValid(newPos):
            return
        
        self._model.slicingPos = newPos
    
    def moveSlicingPosition(self, newPos, oldPos):
        for i in range(3):
            if newPos[i] != oldPos[i]:
                self._updateSlice(self._model.slicingPos[i], i)
        self._updateSliceIntersection()
        
        #when scrolling fast through the stack, we don't want to update
        #the 3d view all the time
        if self._view3d is None:
            return
        def maybeUpdateSlice(oldSlicing):
            if oldSlicing == self._model.slicingPos:
                for i in range(3):
                    self._view3d.ChangeSlice(self._model.slicingPos[i], i)
        QTimer.singleShot(50, partial(maybeUpdateSlice, self._model.slicingPos))
                    
    def changeTime(self, newTime):
        for i in range(3):
            for src in self._sliceSources[i]:
                src.setThrough(0, newTime)
    
    def changeChannel(self, newChannel):
        for i in range(3):
            for src in self._sliceSources[i]:
                src.setThrough(2, newChannel)

    def changeSliceRelative(self, delta, axis):
        """
        Change slice along a certain axis relative to current slice.

        delta -- add delta to current slice position [positive or negative int]
        axis  -- along which axis [0,1,2]
        """
        
        if delta == 0:
            return
        newSlice = self._model.slicingPos[axis] + delta
        if newSlice < 0 or newSlice >= self._model.volumeExtent(axis):
            return
        newPos = copy.copy(self._model.slicingPos)
        newPos[axis] = newSlice
        
        cursorPos = copy.copy(self._model.cursorPos)
        cursorPos[axis] = newSlice
        self._model.cursorPos  = cursorPos  

        self._model.slicingPos = newPos

    def changeSliceAbsolute(self, value, axis):
        """
        Change slice along a certain axis.

        value -- slice number
        axis  -- along which axis [0,1,2]
        """
        
        if value < 0 or value > self._model.volumeExtent(axis):
            return
        newPos = copy.copy(self._model.slicingPos)
        newPos[axis] = value
        if not self._positionValid(newPos):
            return
        
        cursorPos = copy.copy(self._model.cursorPos)
        cursorPos[axis] = value
        self._model.cursorPos  = cursorPos  
        
        self._model.slicingPos = newPos
    
    def settleSlicingPosition(self, settled):
        for v in self._views:
            v.indicateSlicingPositionSettled(settled)

    def positionCursor(self, x, y, axis):
        """
        Change position of the crosshair cursor.

        x,y  -- cursor position on a certain image scene
        axis -- perpendicular axis [0,1,2]
        """
        
        #we get the 2D coordinates x,y from the view that
        #shows the projection perpendicular to axis
        #set this view as active
        self._model.activeView = axis
        
        newPos = [x,y]
        newPos.insert(axis, self._model.slicingPos[axis])

        if newPos == self._model.cursorPos:
            return
        if not self._positionValid(newPos):
            return

        self._model.cursorPos = newPos

            
    def beginDrawing(self, imageview, pos):
        imageview.mousePos = pos
        self._isDrawing  = True
        self._brushingModel.beginDrawing(pos, imageview.sliceShape)

    def endDrawing(self, imageview, pos): 
        self._isDrawing = False
        self._brushingModel.endDrawing(pos)
    
    #private functions ########################################################
    
    def _updateCrossHairCursor(self):
        y,x = posView2D(self._model.cursorPos, axis=self._model.activeView)
        self._views[self._model.activeView]._crossHairCursor.showXYPosition(x,y)
        for i, v in enumerate(self._views):
            v._crossHairCursor.setVisible( self._model.activeView == i )
    
    def _updateSliceIntersection(self):
        for axis, v in enumerate(self._views):
            y,x = posView2D(self._model.slicingPos, axis)
            v._sliceIntersectionMarker.setPosition(x,y)

    def _updateSlice(self, num, axis):
        if num < 0 or num >= self._model.volumeExtent(axis):
            raise Exception("NavigationControler._setSlice(): invalid slice number = %d not in range [0,%d)" % (num, self._model.volumeExtent(axis)))
        #FIXME: Shouldnt the hud listen to the model changes itself?
        self._views[axis].hud.sliceSelector.setValue(num)

        #re-configure the slice source
        for src in self._sliceSources[axis]:
            src.setThrough(1, num)

    def _positionValid(self, pos):
        for i in range(3):
            if pos[i] < 0 or pos[i] >= self._model.shape[i]:
                return False
        return True

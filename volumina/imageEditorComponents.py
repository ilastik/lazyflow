#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import Qt, QPointF, QSize, pyqtSignal, QEvent, QObject, QTimer, QRectF           
from PyQt4.QtGui import QLabel, QPen, QPainter, QPixmap, QHBoxLayout, \
                        QFont, QPainterPath, QBrush, QSpinBox, QAbstractSpinBox, \
                        QSizePolicy, QWidget, QVBoxLayout, QColor

class ImageView2DDockWidget(QWidget):
    def __init__(self, graphicsView):
        QWidget.__init__(self)
        
        self.graphicsView = graphicsView
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.windowForGraphicsView = QWidget()
        self.windowForGraphicsView.layout = QVBoxLayout()
        self.windowForGraphicsView.layout.setContentsMargins(0, 0, 0, 0)
        self.windowForGraphicsView.setLayout(self.windowForGraphicsView.layout)
    
        self.addGraphicsView()
    
    def addGraphicsView(self):
        self.layout.addWidget(self.graphicsView)
        
    def removeGraphicsView(self):
        self.layout.removeWidget(self.graphicsView)
        
class ImageViewWidget(QWidget):
    def __init__(self, parent, view):
        QWidget.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.installEventFilter(self)
               
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(0)
         
        self.imageView2D = view
         
        self.main = ImageView2DDockWidget(self.imageView2D)
        self.layout.addWidget(self.main)

    def addStatusBar(self, bar):
        self.statusBar = bar
        self.layout.addLayout(self.statusBar)
        
    def setGrayScaleToQuadStatusBar(self, gray):
        self.quadViewStatusBar.setGrayScale(gray)
    
class SingleStatusBar(QHBoxLayout):
    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)   
        
    def createSingleStatusBar(self, xbackgroundColor, xforegroundColor, ybackgroundColor, yforegroundColor, graybackgroundColor, grayforegroundColor):             
        
        self.xLabel = QLabel()
        self.xLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.xLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(xbackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(xforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "X")
        brush = QBrush(xforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.xLabel.setPixmap(pixmap)
        self.ySpinBox = QSpinBox()
        self.ySpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ySpinBox.setEnabled(False)
        self.ySpinBox.setAlignment(Qt.AlignCenter)
        self.ySpinBox.setToolTip("ySpinBox")
        self.ySpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.ySpinBox.setMaximumHeight(20)
        self.ySpinBox.setMaximum(9999)
        font = self.ySpinBox.font()
        font.setPixelSize(14)
        self.ySpinBox.setFont(font)
        self.ySpinBox.setStyleSheet("QSpinBox { color: " + str(xforegroundColor.name()) + "; font: bold; background-color: " + str(xbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.ySpinBox)
        
        self.yLabel = QLabel()
        self.yLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.yLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(ybackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(yforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Y")
        brush = QBrush(yforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.yLabel.setPixmap(pixmap)
        self.xSpinBox = QSpinBox()
        self.xSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.xSpinBox.setEnabled(False)
        self.xSpinBox.setAlignment(Qt.AlignCenter)
        self.xSpinBox.setToolTip("xSpinBox")
        self.xSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.xSpinBox.setMaximumHeight(20)
        self.xSpinBox.setMaximum(9999)
        font = self.xSpinBox.font()
        font.setPixelSize(14)
        self.xSpinBox.setFont(font)
        self.xSpinBox.setStyleSheet("QSpinBox { color: " + str(yforegroundColor.name()) + "; font: bold; background-color: " + str(ybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.xSpinBox)
        self.addStretch()
            
    def setMouseCoords(self, x, y):
        self.xSpinBox.setValue(x)
        self.ySpinBox.setValue(y)

#*******************************************************************************
# P o s i t i o n M o d e l                                                    *
#*******************************************************************************

class PositionModel(QObject):
    """
    Currently viewed position within a 2D data volume
    (x,y).
    By writing into the public properties of the PositionModel,
    the user can manipulate the volume viewer by writing code
    in the same way as would be possible by manipulating the
    viewer with a mouse.
    """
    
    cursorPositionChanged  = pyqtSignal(object, object)
    
    scrollDelay = 300
    
    def __init__(self, shape2D, parent=None):
        QObject.__init__(self, parent)
        
        #init property fields
        self._cursorPos  = [0,0]
        self._channel    = 0
        self._shape2D    = shape2D
        """
        Since its only one view, activeView is set to 0 be default
        """
        self.activeView = 0
        self._scrollTimer = QTimer()
        self._scrollTimer.setInterval(self.scrollDelay)
        self._scrollTimer.setSingleShot(True)
        self._scrollTimer.timeout.connect(self._onScrollTimer)
        
    @property
    def shape( self ):
        """
        the spatial shape
        """
        return self._shape2D
    
    @property
    def cursorPos(self):
        """
        Returns the spatial position (x,y) that is defined by the position of
        the mouse.
        """
        return self._cursorPos
    
    @cursorPos.setter
    def cursorPos(self, coordinates):
        if coordinates == self._cursorPos:
            return
        oldPos = self._cursorPos
        self._cursorPos = coordinates
        self.cursorPositionChanged.emit(self.cursorPos, oldPos)
    
    def _onScrollTimer(self):
        print "settled"
        self._slicingSettled = True
        self.slicingPositionSettled.emit(True)
#*******************************************************************************
# N a v i g a t i o n I n t e r p r e t e r                                    *
#*******************************************************************************

class   NavigationInterpreter(QObject):
    """
    Provides slots to listens to mouse/keyboard events from one slice view.

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
        self._navCtrl.drawingEnabled = False

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
            self.onMouseDblClickEvent( watched, event )
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
            print imageview._deltaPan.x(),imageview._deltaPan.y()
        
            return
        if imageview._ticker.isActive():
            #the view is still scrolling
            #do nothing until it comes to a complete stop
            return
        
        imageview.mousePos = mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        oldX, oldY = imageview.x, imageview.y
        x = imageview.x = mousePos.x()
        y = imageview.y = mousePos.y()
        self._navCtrl.positionCursor(x, y)
    
    def onMousePressEvent( self, imageview, event ):
        if event.button() == Qt.LeftButton:
            imageview._dragMode = True
            imageview._lastPanPoint = event.pos()
        
    def onMouseReleaseEvent( self, imageview, event ):
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
            
        if event.button() == Qt.LeftButton:
            imageview._dragMode = False
            if imageview._isRubberBandZoom:
                imageview.setDragMode(QGraphicsView.NoDrag)
                rect = QRectF(imageview.mapToScene(self._rubberBandStart), imageview.mapToScene(event.pos()))
                imageview.fitInView(rect, Qt.KeepAspectRatio)
                imageview._isRubberBandZoom = False
                width, height = imageview.size().width() / rect.width(), imageview.height() / rect.height()
                imageview._zoomFactor = min(width, height)
                imageview.setCursor(imageview._cursorBackup)
                return

    def onWheelEvent( self, imageview, event ):
        k_ctrl = (event.modifiers() == Qt.ControlModifier)

        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))

        sceneMousePos = imageview.mapToScene(event.pos())
        grviewCenter  = imageview.mapToScene(imageview.viewport().rect().center())

        if event.delta() > 0:
            if k_ctrl:
                imageview.zoomIn()
            
        else:
            if k_ctrl:
                imageview.zoomOut()
            
        if k_ctrl:
            mousePosAfterScale = imageview.mapToScene(event.pos())
            offset = sceneMousePos - mousePosAfterScale
            newGrviewCenter = grviewCenter + offset
            imageview.centerOn(newGrviewCenter)
            self.onMouseMoveEvent( imageview, event)

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
    
    @property
    def axisColors( self ):
        return self._axisColors
    @axisColors.setter
    def axisColors( self, colors ):
        self._axisColors = colors
        if self._view.imageViewWidget:
            self._view.imageViewWidget.bgColor = self.axisColors[0]
        
    def __init__(self, imageView2D, sliceSources, positionModel, brushingModel):
        QObject.__init__(self)
        
        # init fields
        self._view = imageView2D
        self._sliceSources = sliceSources
        self._model = positionModel
        self._beginStackIndex = 0
        self._endStackIndex   = 1

        self.drawingEnabled = False
        self._isDrawing = False
        self._tempErase = False
        self._brushingModel = brushingModel

        self.axisColors = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]
    
    def moveCrosshair(self, newPos, oldPos):
        self._updateCrossHairCursor()

    def positionCursor(self, x, y):
        """
        Change position of the crosshair cursor.
        x,y  -- cursor position on a certain image scene
        """
        newPos = [x,y]
        if newPos == self._model.cursorPos:
            return
        if not self._positionValid(newPos):
            return
        self._model.cursorPos = newPos            
    #private functions ########################################################
    
    def _updateCrossHairCursor(self):
        y,x = self._model.cursorPos
        self._view._crossHairCursor.showXYPosition(x,y)
        self._view._crossHairCursor.setVisible(True)
    
    def _positionValid(self, pos):
        for i in range(2):
            if pos[i] < 0 or pos[i] >= self._model.shape[i]:
                return False
        return True
    

from PyQt4.QtCore import QPoint, QPointF, QTimer, pyqtSignal, Qt
from PyQt4.QtGui import QCursor, QGraphicsView, QPainter, QVBoxLayout, QApplication


from crossHairCursor import CrossHairCursor

#*******************************************************************************
# I m a g e V i e w 2 D                                                        *
#*******************************************************************************

class ImageView2D(QGraphicsView):
    focusChanged = pyqtSignal()
    """
    Shows a ImageScene2D to the user and allows for interactive
    scrolling, panning, zooming etc.

    """
    @property
    def sliceShape(self):
        """
        (width, height) of the scene.
        Specifying the shape is necessary to allow for correct
        scrollbars
        """
        return self._sliceShape
    @sliceShape.setter
    def sliceShape(self, s):
        self._sliceShape = s
        sceneShape = (s[1], s[0])
        self.scene().sceneShape                  = sceneShape
        self._crossHairCursor.sceneShape         = sceneShape
           
    @property
    def imageViewWidget(self):
        return self._imageViewWidget
    @imageViewWidget.setter
    def imageViewWidget(self, imageViewWidget):
        """
        Sets up a imageViewWidget
        
        imageViewWidget -- a QWidget
        """
        
        self._imageViewWidget = imageViewWidget
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self._imageViewWidget)
        self.layout().addStretch()
    
    def setImageViewWidget(self,imageViewWidget):
        self._imageViewWidget = imageViewWidget
    
    def __init__(self, imagescene2d):
        """
        Constructs a view upon a ImageScene2D
        
        imagescene2d -- a ImgeScene2D instance
        """
        
        QGraphicsView.__init__(self)
        self.setScene(imagescene2d)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._isRubberBandZoom = False
        self._cursorBackup = None
        
        #these attributes are exposed as public properties above
        self._sliceShape  = None #2D shape of this view's shown image
        self._slices = None #number of slices that are stacked
        self._imageViewWidget    = None
        
        self._crossHairCursor         = None
        self._sliceIntersectionMarker = None

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tickerEvent)
        
        #
        # Setup the Viewport for fast painting
        #
        #With these flags turned on we could handle the drawing of the
        #white background ourselves thus removing the flicker
        #when scrolling fast through the slices
        #self.viewport().setAttribute(Qt.WA_OpaquePaintEvent)
        #self.viewport().setAttribute(Qt.WA_NoSystemBackground)
        #self.viewport().setAttribute(Qt.WA_PaintOnScreen)
        #self.viewport().setAutoFillBackground(False)
        
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        #as rescaling images is slow if done in software,
        #we use Qt's built-in background caching mode so that the cached
        #image need only be blitted on the screen when we only move
        #the cursor
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHint(QPainter.Antialiasing, False)

        self._crossHairCursor = CrossHairCursor(self.scene())
        self._crossHairCursor.setZValue(99)
        
        
 
        #FIXME: this should be private, but is currently used from
        #       within the image scene renderer
        self.tempImageItems = []
        
        self._zoomFactor = 1.0
        
        #for panning
        self._lastPanPoint = QPoint()
        self._dragMode = False
        self._deltaPan = QPointF(0,0)
        
        #Unfortunately, setting the style like this make the scroll bars look
        #really crappy...
        #self.setStyleSheet("QWidget:!focus { border: 2px solid " + self._axisColor[self._axis].name() +"; border-radius: 4px; }\
        #                    QWidget:focus { border: 2px solid white; border-radius: 4px; }")

        #FIXME: Is there are more elegant way to handle this?

        self.setMouseTracking(True)

        # invisible cursor to enable custom cursor
        self._hiddenCursor = QCursor(Qt.BlankCursor)
        # For screen recording BlankCursor doesn't work
        #self.hiddenCursor = QCursor(Qt.ArrowCursor)  
        
    def _cleanUp(self):        
        self._ticker.stop()
        del self._ticker

    def indicateSlicingPositionSettled(self, settled):
        self.scene().indicateSlicingPositionSettled(settled)

    def viewportRect(self):
        """
        Return a QRectF giving the part of the scene currently displayed in this
        widget's viewport in the scene's coordinates
        """
        return self.mapToScene(self.viewport().geometry()).boundingRect()
   
    def mapScene2Data(self, pos):
        return self.scene().scene2data.map(pos)
   
    # We have to overload some QGraphicsView event handlers with a nop to make the event switch work.
    # Otherwise, the events are not catched by our eventFilter.
    # There is no real reason for this behaviour: seems to be just a quirky qt implementation detail.
    def mouseMoveEvent(self, event):
        event.ignore()
    def mouseReleaseEvent(self, event):
        event.ignore()
    def mouseDoubleClickEvent( self, event):
        event.ignore()
    def wheelEvent(self, event):
        event.ignore()

    def _panning(self):
        hBar = self.horizontalScrollBar()
        vBar = self.verticalScrollBar()
        vBar.setValue(vBar.value() - self._deltaPan.y())
        if self.isRightToLeft():
            hBar.setValue(hBar.value() + self._deltaPan.x())
        else:
            hBar.setValue(hBar.value() - self._deltaPan.x())
        
    def _deaccelerate(self, speed, a=1, maxVal=64):
        x = self._qBound(-maxVal, speed.x(), maxVal)
        y = self._qBound(-maxVal, speed.y(), maxVal)
        ax ,ay = self._setdeaccelerateAxAy(speed.x(), speed.y(), a)
        if x > 0:
            x = max(0.0, x - a*ax)
        elif x < 0:
            x = min(0.0, x + a*ax)
        if y > 0:
            y = max(0.0, y - a*ay)
        elif y < 0:
            y = min(0.0, y + a*ay)
        return QPointF(x, y)

    def _qBound(self, minVal, current, maxVal):
        """PyQt4 does not wrap the qBound function from Qt's global namespace
           This is equivalent."""
        return max(min(current, maxVal), minVal)
    
    def _setdeaccelerateAxAy(self, x, y, a):
        x = abs(x)
        y = abs(y)
        if x > y:
            if y > 0:
                ax = int(x / y)
                if ax != 0:
                    return ax, 1
            else:
                return x/a, 1
        if y > x:
            if x > 0:
                ay = int(y/x)
                if ay != 0:
                    return 1, ay
            else:
                return 1, y/a
        return 1, 1

    def _tickerEvent(self):
        if self._deltaPan.x() == 0.0 and self._deltaPan.y() == 0.0 or self._dragMode == True:
            self._ticker.stop()
        else:
            self._deltaPan = self._deaccelerate(self._deltaPan)
            self._panning()

    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def fitImage(self):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        width, height = self.size().width() / self.sceneRect().width(), self.height() / self.sceneRect().height()
        self._zoomFactor = min(width, height)
                
    def centerImage(self):
        self.centerOn(self.sceneRect().width()/2 + self.sceneRect().x(), self.sceneRect().height()/2 + self.sceneRect().y()) 
        
    def toggleImageViewWidget(self):
        if self._imageViewWidget.isVisible():
            self._imageViewWidget.setVisible(False)
        else:
            self._imageViewWidget.setVisible(True)
            
    def hideImageViewWidget(self, hide):
        self._imageViewWidget.setVisible(hide)
    
    def focusInEvent(self, event):
        self.focusChanged.emit()
        
    def focusOutEvent(self, event):
        pass
     
    def changeViewPort(self,qRectf):
        self.fitInView(qRectf,mode = Qt.KeepAspectRatio)
        width, height = self.size().width() / qRectf.width(), self.height() / qRectf.height()
        self._zoomFactor = min(width, height)

    def doScale(self, factor):
        self._zoomFactor = self._zoomFactor * factor
        self.scale(factor, factor)
        
    def doScaleTo(self, zoom=1):
        factor = ( 1 / self._zoomFactor ) * zoom
        self._zoomFactor = zoom
        self.scale(factor, factor)
        

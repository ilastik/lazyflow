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

from PyQt4.QtCore import Qt, pyqtSignal, QPointF, QSize
from PyQt4.QtGui import QSizePolicy, QWidget, QVBoxLayout
            
from PyQt4.QtGui import QLabel, QPen, QPainter, QPixmap, QHBoxLayout, \
                        QFont, QPainterPath, QBrush, QSpinBox, QAbstractSpinBox, \
                        QCheckBox
import numpy


class ImageView2DFloatingWindow(QWidget):
    onCloseClick = pyqtSignal()
    def __init__(self):
        QWidget.__init__(self)
        
    def closeEvent(self, event):
        self.onCloseClick.emit()
        event.ignore()

class ImageView2DDockWidget(QWidget):
    def __init__(self, graphicsView):
        QWidget.__init__(self)
        
        self.graphicsView = graphicsView
        self._isDocked = True
        self._isMaximized = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.windowForGraphicsView = ImageView2DFloatingWindow()
        self.windowForGraphicsView.layout = QVBoxLayout()
        self.windowForGraphicsView.layout.setContentsMargins(0, 0, 0, 0)
        self.windowForGraphicsView.setLayout(self.windowForGraphicsView.layout)
        
    
        self.addGraphicsView()
    
    def connectHud(self):
        self.graphicsView._hud.dockButtonClicked.connect(self.onDockButton)
        self.graphicsView._hud.maximizeButtonClicked.connect(self.onMaxButton)
        
    def addGraphicsView(self):
        self.layout.addWidget(self.graphicsView)
        
    def removeGraphicsView(self):
        self.layout.removeWidget(self.graphicsView)
        
    def undockView(self):
        self._isDocked = False
        self.graphicsView._hud.dockButton.setDockIcon()
        self.graphicsView._hud.maxButton.setEnabled(False)
        
        self.removeGraphicsView()
        self.windowForGraphicsView.layout.addWidget(self.graphicsView)
        self.windowForGraphicsView.show()
        self.windowForGraphicsView.raise_()
    
        
        self.windowForGraphicsView.layout.removeWidget(self.graphicsView)
        self.windowForGraphicsView.hide()
        self.addGraphicsView()

class SingleTool(object):
    def embed2Din5D(self,twoDArray):
        m,n=twoDArray.shape
        fiveDArray = numpy.zeros((1,1,m,n,1))
        fiveDArray[0,0,:,:,0] = twoDArray
        return fiveDArray

class SingleView(QWidget):
    def __init__(self, parent, view1):
        QWidget.__init__(self, parent)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.installEventFilter(self)
               
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(0)
         
        self.imageView2D_1 = view1
         
        self.dock_main = ImageView2DDockWidget(self.imageView2D_1)
        self.layout.addWidget(self.dock_main)

    def addStatusBar(self, bar):
        self.statusBar = bar
        self.layout.addLayout(self.statusBar)
        
    def setGrayScaleToQuadStatusBar(self, gray):
        self.quadViewStatusBar.setGrayScale(gray)
        
    def setMouseCoordsToQuadStatusBar(self, x, y, z):
        self.quadViewStatusBar.setMouseCoords1(x,y)
        
    
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
        self.xSpinBox.setStyleSheet("QSpinBox { color: " + str(xforegroundColor.name()) + "; font: bold; background-color: " + str(xbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.xSpinBox)
        
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
        self.ySpinBox.setStyleSheet("QSpinBox { color: " + str(yforegroundColor.name()) + "; font: bold; background-color: " + str(ybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.ySpinBox)
        self.addStretch()
            
    def setMouseCoords(self, x, y, z):
        self.xSpinBox.setValue(z)
        self.ySpinBox.setValue(y)

from PyQt4.QtCore import QObject, QTimer

#*******************************************************************************
# P o s i t i o n M o d e l                                                    *
#*******************************************************************************

class PositionModel(QObject):
    """
    Currently viewed position within a 5D data volume
    (time, x,y,z, channels).
    
    By writing into the public properties of the PositionModel,
    the user can manipulate the volume viewer by writing code
    in the same way as would be possible by manipulating the
    viewer with a mouse.
    """
    
    channelChanged         = pyqtSignal(int)
    cursorPositionChanged  = pyqtSignal(object, object)
    slicingPositionChanged = pyqtSignal(object, object)
    slicingPositionSettled = pyqtSignal(bool)
    
    scrollDelay = 300
    
    def __init__(self, shape5D, parent=None):
        QObject.__init__(self, parent)
        
        assert len(shape5D) == 5
        
        #init property fields
        self._cursorPos  = [0,0,0]
        self._slicingPos = [0,0,0]

        self._channel    = 0
        self._shape5D    = shape5D
        
        """
        Index of the currently active view in [0,1,2].
        A view is active when the mouse cursor hovered over it last.
        """
        self.activeView = 0

        #call property setters to trigger updates etc. 
        self.cursorPos   = self._cursorPos
        self.slicingPos  = self._slicingPos
        self.channel     = self._channel
        
        self._scrollTimer = QTimer()
        self._scrollTimer.setInterval(self.scrollDelay)
        self._scrollTimer.setSingleShot(True)
        self._scrollTimer.timeout.connect(self._onScrollTimer)
        
        self._slicingSettled = True
        
    def sliceShape(self, axis):
        """
        returns the 2D shape of slices perpendicular to axis
        """
        shape = self._shape5D[1:4]
        if len(shape) == 2:
            return shape
        else:
            shape = list(shape)
            del shape[axis]
            return numpy.asarray(shape)
    
    @property
    def shape( self ):
        """
        the spatial shape
        """
        return self._shape5D[1:4]
        
    @property    
    def time( self ):
        """
        the currently shown index of the time dimension
        """
        return self._time
    @time.setter
    def time( self, value ):
        if value < 0 or value >= self._shape5D[0] or value == self._time:
            return
        self._time = value    
        self.timeChanged.emit(value)

    @property
    def channel( self ):
        """
        the currently shown index of the channel dimension
        """
        return self._channel
    @channel.setter
    def channel(self, value):
        if value < 0 or value >= self._shape5D[4] or value == self._channel:
            return
        self._channel = value    
        self.channelChanged.emit(value)
    
    @property
    def cursorPos(self):
        """
        Returns the spatial position (x,y,z) that is defined by
        the slice number of the slice under the cursor and the position
        on the cursor on that slice.
        Notice the difference to `slicingPos`.
        """
        return self._cursorPos
    @cursorPos.setter
    def cursorPos(self, coordinates):
        if coordinates == self._cursorPos:
            return
        oldPos = self._cursorPos
        self._cursorPos = coordinates
        self.cursorPositionChanged.emit(self.cursorPos, oldPos)
    
    @property
    def slicingPos(self):
        """
        Returns the spatial position (x,y,z) that the volume viewer is currently
        configured to show.
        Notice the difference to `cursorPos`. Here, we mean the position as defined
        by the three slice views.
        """
        return self._slicingPos
    @slicingPos.setter
    def slicingPos(self, pos):
        if pos == self._slicingPos:
            return
        oldPos = self._slicingPos
        
        self._slicingPos = pos
        
        if self._slicingSettled:
            print "unsettle"
            self._slicingSettled = False
            self.slicingPositionSettled.emit(False)
        self._scrollTimer.start()
        
        self.slicingPositionChanged.emit(self.slicingPos, oldPos)
        
    def _onScrollTimer(self):
        print "settled"
        self._slicingSettled = True
        self.slicingPositionSettled.emit(True)
        
from PyQt4.QtCore import QEvent
from PyQt4.QtGui  import QColor
import  copy

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
        self._navCtrl.drawingEnabled = False

    def finalize( self ):
        pass

    def eventFilter( self, watched, event ):
        etype = event.type()
        if etype == QEvent.MouseMove:
            self.onMouseMoveEvent( watched, event )
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
        if imageview._ticker.isActive():
            #the view is still scrolling
            #do nothing until it comes to a complete stop
            return
        
        imageview.mousePos = mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        oldX, oldY = imageview.x, imageview.y
        x = imageview.x = mousePos.x()
        y = imageview.y = mousePos.y()
        self._navCtrl.positionCursor(x, y)


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
        self._view._sliceIntersectionMarker.setColor(self.axisColors[2], self.axisColors[1])
        if self._view.hud:
            self._view.hud.bgColor = self.axisColors[0]
        
#        for axis, v in enumerate(self._views):
#            #FIXME: Bad dependency here on hud to be available!
#            if v.hud: v.hud.bgColor = self.axisColors[axis]
#        
        
    def __init__(self, imageView2D, sliceSources, positionModel, brushingModel, time = 0, channel = 0, view3d=None):
        QObject.__init__(self)
        
        # init fields
        self._view = imageView2D
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

        
                    
    def changeChannel(self, newChannel):
        for i in range(3):
            for src in self._sliceSources[i]:
                src.setThrough(2, newChannel)

    def positionCursor(self, x, y):
        """
        Change position of the crosshair cursor.

        x,y  -- cursor position on a certain image scene
        axis -- perpendicular axis [0,1,2]
        """
        
        #we get the 2D coordinates x,y from the view that
        #shows the projection perpendicular to axis
        #set this view as active
        
        newPos = [x,y]
        newPos.insert(0, self._model.slicingPos[0])

        if newPos == self._model.cursorPos:
            return
        if not self._positionValid(newPos):
            return

        self._model.cursorPos = newPos

            
    
    #private functions ########################################################
    
    def _updateCrossHairCursor(self):
        y,x = posView2D(self._model.cursorPos, axis=self._model.activeView)
        self._view._crossHairCursor.showXYPosition(x,y)
        self._view._crossHairCursor.setVisible(self._model.activeView == 0)
    
    def _positionValid(self, pos):
        for i in range(3):
            if pos[i] < 0 or pos[i] >= self._model.shape[i]:
                return False
        return True
from PyQt4.QtCore import QObject
from abc import ABCMeta, abstractmethod

from pixelpipeline.asyncabcs import _has_attributes

class InterpreterABC:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def start( self ):
        '''Hook method called after installed as an event filter.'''

    @abstractmethod    
    def finalize( self ):
        '''Hook method called just before deinstall as an event filter.'''

    @abstractmethod    
    def eventFilter( self, watched, event ):
        '''Necessary to act as a Qt event filter. '''

    @classmethod
    def __subclasshook__(cls, C):
        if cls is InterpreterABC:
            if _has_attributes(C, ['start', 'finalize', 'eventFilter']):
                return True
            return False
        return NotImplemented




class EventSwitch( QObject ):
    @property
    def interpreter( self ):
        return self._interpreter

    @interpreter.setter
    def interpreter( self, interpreter ):
        assert(isinstance(interpreter, InterpreterABC))
        # finalize old interpreter before deinstalling to
        # avoid inconsistencies when eventloop and eventswitch
        # are running in different threads
        if self._interpreter:
            self._interpreter.finalize()

        self._imageViews.removeEventFilter(self._interpreter)
        if interpreter:
            self._imageViews.installEventFilter(interpreter)

        
        
        self._interpreter = interpreter

        # start the new interpreter after installing 
        # to avoid inconcistencies
        self._interpreter.start()

    def __init__( self, imageviews, interpreter=None):
        super(EventSwitch, self).__init__()
        self._imageViews = imageviews
        self._interpreter = None
        if interpreter:
            self.interpreter = interpreter

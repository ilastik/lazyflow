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
from eventswitch import InterpreterABC

#*******************************************************************************
# I m a g e V i e w W i d g e t                                                * 
#*******************************************************************************

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
         
        self.layout.addWidget(self.imageView2D)

    def addStatusBar(self, bar):
        self.statusBar = bar
        self.layout.addLayout(self.statusBar)
        
#*******************************************************************************
# P o s i t i o n S t a t u s B a r 2 D                                        *
#*******************************************************************************

class PositionStatusBar2D(QHBoxLayout):
    """Widget displaying x, y coordinate plus current gray value."""

    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)   
        
    def create(self, xbackgroundColor, xforegroundColor, ybackgroundColor, yforegroundColor, graybackgroundColor, grayforegroundColor):             
        
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
    
    def updateCoordLabels(self, pos):
        self.xSpinBox.setValue(pos[0])
        self.ySpinBox.setValue(pos[1])
            

#*******************************************************************************
# P o s i t i o n M o d e l                                                    *
#*******************************************************************************

class PositionModelImage(QObject):
    """
    Currently viewed position within a 2D data volume
    (x,y).
    By writing into the public properties of the PositionModel,
    the user can manipulate the volume viewer by writing code
    in the same way as would be possible by manipulating the
    viewer with a mouse.
    """
    
    cursorPositionChanged  = pyqtSignal(object, object)
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        
        #init property fields
        self._cursorPos  = [0,0]
        self._channel    = 0
        self._shape2D    = None
        
    @property
    def shape( self ):
        """
        the spatial shape
        """
        return self._shape2D
    @shape.setter
    def shape( self, s ):
        self._shape2D = s
    
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
    
#*******************************************************************************
# N a v i g a t i o n I n t e r p r e t e r                                    *
#*******************************************************************************

class   NavigationInterpreterImage(QObject):
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

    def stop( self ):
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
            self.onMouseButtonDblClickEvent( watched, event )
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
    
    def onMousePressEvent( self, imageview, event ):
        if event.button() == Qt.LeftButton:
            imageview._dragMode = True
            imageview._lastPanPoint = event.pos()
        
    def onMouseReleaseEvent( self, imageview, event ):
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
            
        if event.button() == Qt.LeftButton:
            imageview._dragMode = False
            
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
assert issubclass(NavigationInterpreterImage, InterpreterABC)    

#*******************************************************************************
# N a v i g a t i o n C o n t r o l e r                                        *
#*******************************************************************************

class NavigationControlerImage(QObject):
    """
    Controler for navigating through the volume.
    
    The NavigationContrler object listens to changes
    in a given PositionModel and updates three slice
    views (representing the spatial X, Y and Z slicings)
    accordingly.
    """
    
    
    @property
    def posModel(self):
        return self._model

    @posModel.setter
    def posModel(self, posM):
        self._model = posM

    
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
        if self._model.shape is None:
            return False
        for i in range(2):
            if pos[i] < 0 or pos[i] >= self._model.shape[i]:
                return False
        return True
    

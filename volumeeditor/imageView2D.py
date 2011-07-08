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

from PyQt4.QtCore import QPoint, QPointF, QRectF, QTimer, pyqtSignal, Qt, \
                         QSize, QRect
from PyQt4.QtOpenGL import QGLWidget, QGLFramebufferObject
from PyQt4.QtGui import *

import numpy
import os.path, time

from patchAccessor import PatchAccessor
from viewManager import ViewManager
from drawManager import DrawManager
from crossHairCursor import CrossHairCursor
from sliceIntersectionMarker import SliceIntersectionMarker
from imageSceneRenderer import ImageSceneRenderer
from imageScene2D import ImageScene2D
from helper import InteractionLogger

#*******************************************************************************
# H u d                                                                        *
#*******************************************************************************

class Hud(QFrame):
    def __init__( self, minimum = 0, maximum = 100, coordinateLabel = "X:", parent = None ):
        super(Hud, self).__init__( parent=parent )

        # init properties
        self._minimum = minimum
        self._maximum = maximum

        # configure self
        #
        # a border-radius of >0px to make the Hud appear rounded
        # does not work together with an QGLWidget, the corners just appear black
        # instead of transparent
        self.setStyleSheet("QFrame {background-color: white; color: black; border-radius: 0px;}")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(3,1,3,1)

        # dimension label
        self.dimLabel = QLabel(coordinateLabel)
        font = self.dimLabel.font()
        font.setBold(True)
        self.dimLabel.setFont(font)
        self.layout().addWidget(self.dimLabel)

        # coordinate selection
        self.sliceSelector = QSpinBox()
        self.sliceSelector.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sliceSelector.setAlignment(Qt.AlignRight)
        self.sliceSelector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)            
        self.sliceSelector.setRange(self._minimum, self._maximum)
        self.layout().addWidget(self.sliceSelector)

        # coordinate label
        self.coordLabel = QLabel("of " + str(self._maximum))
        self.layout().addWidget(self.coordLabel)


#*******************************************************************************
# I m a g e V i e w 2 D                                                        *
#*******************************************************************************
#TODO: ImageView2D should not care/know about what axis it is!
class ImageView2D(QGraphicsView):
    sliceChanged       = pyqtSignal(int,int)
    drawing            = pyqtSignal(int, QPointF)
    beginDraw          = pyqtSignal(int, QPointF)
    endDraw            = pyqtSignal(int, QPointF)
    mouseMoved         = pyqtSignal(int, int, int, bool)
    mouseDoubleClicked = pyqtSignal(int, int, int)
    
    axisColor = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]
    blockSize = 128
    
    @property
    def sliceNumber(self):
        return self._viewManager.position[self._axis]
    
    @property
    def sliceExtent(self):
        return self._viewManager.imageExtent(self._axis)
    
    @property
    def shape2D(self):
        return self._viewManager.imageShape(self._axis)
    
    def initializeGL(self):
        self.scene().initializeGL()
   
    def initConnects(self):
        self._viewManager.sliceChanged.connect(self.onSliceChange)
    
    def onSliceChange(self, num, axis):
        if axis != self._axis: return
        
        print "ImageView2D.onSliceChange", num, axis
        
        if not self._useGL:
            #reset the background cache
            self.resetCachedContent()
        #make sure all tiles are regenerated
        self.scene().markTilesDirty()
        
        #FIXME: this whole section needs porting
        #
        #Here, we need access to the overlay widget because it is not separated
        #yet into a model - view part...
        image = None
        overlays = []
        
        if not self.porting_overlaywidget:
            return
        
        for item in reversed(self.porting_overlaywidget.overlays):
            if item.visible:
                overlays.append(item.getOverlaySlice(self._viewManager.slicePosition[self._axis], self._axis, self._viewManager.time, item.channel))
        if len(self.porting_overlaywidget.overlays) == 0 \
           or self.porting_overlaywidget.getOverlayRef("Raw Data") is None:
            return
        
        rawData = self.porting_overlaywidget.getOverlayRef("Raw Data")._data
        image = rawData.getSlice(self._viewManager.slicePosition[self._axis],\
                                 self._axis, self._viewManager.time,\
                                 self.porting_overlaywidget.getOverlayRef("Raw Data").channel)

        self.porting_image = image
        self.porting_overlays = overlays
        
        self.scene()._imageSceneRenderer.renderImage(self.viewportRect(), image, overlays)   
   
    def __init__(self, axis, viewManager, drawManager, useGL=False):
        """
        imShape: 3D shape of the block that this slice view displays.
                 first two entries denote the x,y extent of one slice,
                 the last entry is the extent in slice direction
        """
        QGraphicsView.__init__(self)
        assert(axis in [0,1,2])
        self._useGL = useGL
        
        #FIXME: for porting
        self.porting_image = None
        self.porting_overlays = None
        self.porting_overlaywidget = None
        
        #
        # Setup the Viewport for fast painting
        #
        if self._useGL:
            self.openglWidget = QGLWidget(self)
            self.setViewport(self.openglWidget)
            #we clear the background ourselves
            self.viewport().setAutoFillBackground(False)
            #QGraphicsView cannot use partial updates when using 
            #an OpenGL widget as a viewport
            #http://doc.qt.nokia.com/qq/qq26-openglcanvas.html
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            self.setScene(ImageScene2D(viewManager.imageShape(axis),  self.viewport()))
            self.initializeGL()
        else:
            self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
            #as rescaling images is slow if done in software,
            #we use Qt's built-in background caching mode so that the cached
            #image need only be blitted on the screen when we only move
            #the cursor
            self.setCacheMode(QGraphicsView.CacheBackground)
            self.setScene(ImageScene2D(viewManager.imageShape(axis)))
        self.setRenderHint(QPainter.Antialiasing, False)
        
        self.drawingEnabled = False
        
        self._drawManager = drawManager
        self._viewManager = viewManager
 
        #FIXME: this should be private, but is currently used from
        #       within the image scene renderer
        self.tempImageItems = []
        
        self._axis = axis
        self._isDrawing = False
        self.border = None
        self.allBorder = None
        self.factor = 1.0
        
        #for panning
        self._lastPanPoint = QPoint()
        self._dragMode = False
        self._deltaPan = QPointF(0,0)
        
        self.fastRepaint = True
        self.drawUpdateInterval = 300

        #Heads up display 
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        axisLabels = ["X:", "Y:", "Z:"]
        self.hud = Hud(0, self.sliceExtent - 1, axisLabels[self._axis])

        self.layout().addWidget(self.hud)
        self.layout().addStretch()
        
        #Unfortunately, setting the style like this make the scroll bars look
        #really crappy...
        #self.setStyleSheet("QWidget:!focus { border: 2px solid " + self._axisColor[self._axis].name() +"; border-radius: 4px; }\
        #                    QWidget:focus { border: 2px solid white; border-radius: 4px; }")

        #FIXME: Is there are more elegant way to handle this?
        if self._axis is 0:
            self.rotate(90.0)
            self.scale(1.0,-1.0)

        self.setMouseTracking(True)

        #indicators for the biggest filter mask's size
        #marks the area where labels should not be placed
        # -> the margin top, left, right, bottom
        self.setBorderMarginIndicator(0)
        # -> the complete 2D slice is marked
        brush = QBrush(QColor(0,0,255))
        brush.setStyle( Qt.DiagCrossPattern )
        allBorderPath = QPainterPath()
        allBorderPath.setFillRule(Qt.WindingFill)
        allBorderPath.addRect(0, 0, *self.shape2D)
        self.allBorder = QGraphicsPathItem(allBorderPath)
        self.allBorder.setBrush(brush)
        self.allBorder.setPen(QPen(Qt.NoPen))
        self.scene().addItem(self.allBorder)
        self.allBorder.setVisible(False)
        self.allBorder.setZValue(99)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self.tickerEvent)
        #label updates while drawing, needed for interactive segmentation
        self.drawTimer = QTimer(self)
        self.drawTimer.timeout.connect(self.notifyDrawing)
        
        # invisible cursor to enable custom cursor
        self.hiddenCursor = QCursor(Qt.BlankCursor)
        
        # For screen recording BlankCursor doesn't work
        #self.hiddenCursor = QCursor(Qt.ArrowCursor)
        
        #self.connect(self, SIGNAL("destroyed()"), self.cleanUp)

        self.crossHairCursor = CrossHairCursor(*self.shape2D)
        self.crossHairCursor.setZValue(100)
        self.scene().addItem(self.crossHairCursor)
        
        #FIXME: do we want to have these connects here or somewhere else?
        self._drawManager.brushSizeChanged.connect(self.crossHairCursor.setBrushSize)
        self._drawManager.brushColorChanged.connect(self.crossHairCursor.setColor)
        
        self.crossHairCursor.setBrushSize(self._drawManager.brushSize)
        self.crossHairCursor.setColor(self._drawManager.drawColor)

        self.sliceIntersectionMarker = SliceIntersectionMarker(*self.shape2D)
        if self._axis == 0:
            self.sliceIntersectionMarker.setColor(self.axisColor[1], self.axisColor[2])
        elif self._axis == 1:
            self.sliceIntersectionMarker.setColor(self.axisColor[0], self.axisColor[2])
        elif self._axis == 2:
            self.sliceIntersectionMarker.setColor(self.axisColor[0], self.axisColor[1])    
        self.scene().addItem(self.sliceIntersectionMarker)
        #FIXME: Use a QAction here so that we do not have to synchronize
        #between this initial state and the toggle button's initial state
        self.sliceIntersectionMarker.setVisibility(True)

        self.tempErase = False

        #initialize connections
        self.initConnects()
           
    def setBorderMarginIndicator(self, margin):
        """
        update the border margin indicator (left, right, top, bottom)
        to reflect the new given margin
        """
        
        self.margin = margin
        if self.border:
            self.scene().removeItem(self.border)
        borderPath = QPainterPath()
        borderPath.setFillRule(Qt.WindingFill)
        borderPath.addRect(0,0, margin, self.shape2D[1])
        borderPath.addRect(0,0, self.shape2D[0], margin)
        borderPath.addRect(self.shape2D[0]-margin,0, margin, self.shape2D[1])
        borderPath.addRect(0,self.shape2D[1]-margin, self.shape2D[0], margin)
        self.border = QGraphicsPathItem(borderPath)
        brush = QBrush(QColor(0,0,255))
        brush.setStyle( Qt.Dense7Pattern )
        self.border.setBrush(brush)
        self.border.setPen(QPen(Qt.NoPen))
        self.border.setZValue(200)
        self.scene().addItem(self.border)

    def setSliceIntersection(self, state):
        self.sliceIntersectionMarker.setVisibility(state)
            
    def updateSliceIntersection(self, num, axis):
        #print "updateSliceIntersection(%d, %d)" % (num, axis)
        if self._axis == 0:
            if axis == 1:
                self.sliceIntersectionMarker.setPositionX(num)
            elif axis == 2:
                self.sliceIntersectionMarker.setPositionY(num)
            else:
                return
        elif self._axis == 1:
            if axis == 0:
                self.sliceIntersectionMarker.setPositionX(num)
            elif axis == 2:
                self.sliceIntersectionMarker.setPositionY(num)
            else:
                return
        elif self._axis == 2:
            if axis == 0:
                self.sliceIntersectionMarker.setPositionX(num)
            elif axis == 1:
                self.sliceIntersectionMarker.setPositionY(num)
            else:
                return   

    def cleanUp(self):        
        self.ticker.stop()
        self.drawTimer.stop()
        del self.drawTimer
        del self.ticker

    def viewportRect(self):
        return self.mapToScene(self.viewport().geometry()).boundingRect()

    def saveSlice(self, filename):
        print "Saving in ", filename, "slice #", self.sliceNumber, "axis", self._axis
        result_image = QImage(self.scene().image.size(), self.scene().image.format())
        p = QPainter(result_image)
        for patchNr in range(self.patchAccessor.patchCount):
            bounds = self.patchAccessor.getPatchBounds(patchNr)
            if self.openglWidget is None:
                p.drawImage(0, 0, self.scene().image)
            else:
                p.drawImage(bounds[0], bounds[2], self.imagePatches[patchNr])
        p.end()
        #horrible way to transpose an image. but it works.
        transform = QTransform()
        transform.rotate(90)
        result_image = result_image.mirrored()
        result_image = result_image.transformed(transform)
        result_image.save(QString(filename))
   
    def notifyDrawing(self):
        self.drawing.emit(self._axis, self.mousePos)
    
    def beginDrawing(self, pos):
        InteractionLogger.log("%f: beginDrawing`()" % (time.clock()))   
        self.mousePos = pos
        self._isDrawing  = True
        line = self._drawManager.beginDrawing(pos, self.shape2D)
        line.setZValue(99)
        self.tempImageItems.append(line)
        self.scene().addItem(line)
        if self.drawUpdateInterval > 0:
            self.drawTimer.start(self.drawUpdateInterval) #update labels every some ms
            
        self.beginDraw.emit(self._axis, pos)
        
    def endDrawing(self, pos):
        InteractionLogger.log("%f: endDrawing()" % (time.clock()))     
        self.drawTimer.stop()
        self._isDrawing = False
        
        self.endDraw.emit(self._axis, pos)

    def wheelEvent(self, event):
        keys = QApplication.keyboardModifiers()
        k_alt = (keys == Qt.AltModifier)
        k_ctrl = (keys == Qt.ControlModifier)

        self.mousePos = self.mapToScene(event.pos())
        grviewCenter  = self.mapToScene(self.viewport().rect().center())

        if event.delta() > 0:
            if k_alt:
                self.changeSlice(10)
            elif k_ctrl:
                scaleFactor = 1.1
                self.doScale(scaleFactor)
            else:
                self.changeSlice(1)
        else:
            if k_alt:
                self.changeSlice(-10)
            elif k_ctrl:
                scaleFactor = 0.9
                self.doScale(scaleFactor)
            else:
                self.changeSlice(-1)
        if k_ctrl:
            mousePosAfterScale = self.mapToScene(event.pos())
            offset = self.mousePos - mousePosAfterScale
            newGrviewCenter = grviewCenter + offset
            self.centerOn(newGrviewCenter)
            self.mouseMoveEvent(event)

    #TODO oli
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor(Qt.SizeAllCursor))
            self._lastPanPoint = event.pos()
            self.crossHairCursor.setVisible(False)
            self._dragMode = True
            if self.ticker.isActive():
                self._deltaPan = QPointF(0, 0)

        if event.buttons() == Qt.RightButton:
            #make sure that we have the cursor at the correct position
            #before we call the context menu
            self.mouseMoveEvent(event)
            self.customContextMenuRequested.emit(event.pos())
            return

        if not self.drawingEnabled:
            print "ImageView2D.mousePressEvent: drawing is not enabled"
            return
        
        if event.buttons() == Qt.LeftButton:
            #don't draw if flicker the view
            if self.ticker.isActive():
                return
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self._drawManager.setErasing()
                self.tempErase = True
            mousePos = self.mapToScene(event.pos())
            self.beginDrawing(mousePos)
            
    #TODO oli
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor())
            releasePoint = event.pos()
            self._lastPanPoint = releasePoint
            self._dragMode = False
            self.ticker.start(20)
        if self._isDrawing:
            mousePos = self.mapToScene(event.pos())
            self.endDrawing(mousePos)
        if self.tempErase:
            self._drawManager.disableErasing()
            self.tempErase = False

    #TODO oli
    def panning(self):
        hBar = self.horizontalScrollBar()
        vBar = self.verticalScrollBar()
        vBar.setValue(vBar.value() - self._deltaPan.y())
        if self.isRightToLeft():
            hBar.setValue(hBar.value() + self._deltaPan.x())
        else:
            hBar.setValue(hBar.value() - self._deltaPan.x())
        self.scene()._imageSceneRenderer.renderImage(self.viewportRect(), self.porting_image, self.porting_overlays)
        
        
    #TODO oli
    def deaccelerate(self, speed, a=1, maxVal=64):
        x = self.qBound(-maxVal, speed.x(), maxVal)
        y = self.qBound(-maxVal, speed.y(), maxVal)
        ax ,ay = self.setdeaccelerateAxAy(speed.x(), speed.y(), a)
        if x > 0:
            x = max(0.0, x - a*ax)
        elif x < 0:
            x = min(0.0, x + a*ax)
        if y > 0:
            y = max(0.0, y - a*ay)
        elif y < 0:
            y = min(0.0, y + a*ay)
        return QPointF(x, y)

    def qBound(self, minVal, current, maxVal):
        """PyQt4 does not wrap the qBound function from Qt's global namespace
           This is equivalent."""
        return max(min(current, maxVal), minVal)
    
    def setdeaccelerateAxAy(self, x, y, a):
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

    #TODO oli
    def tickerEvent(self):
        if self._deltaPan.x() == 0.0 and self._deltaPan.y() == 0.0 or self._dragMode == True:
            self.ticker.stop()
            cursor = QCursor()
            mousePos = self.mapToScene(self.mapFromGlobal(cursor.pos()))
            x = mousePos.x()
            y = mousePos.y()
            self.crossHairCursor.showXYPosition(x, y)
        else:
            self._deltaPan = self.deaccelerate(self._deltaPan)
            self.panning()
    
    def coordinateUnderCursor(self):
        """returns the coordinate that is defined by hovering with the mouse
           over one of the slice views. It is _not_ the coordinate as defined
           by the three slice views"""
        width, height = self.shape2D
        validArea = self.x > 0 and self.x < width and self.y > 0 and self.y < height
        if not validArea:
            posX = posY = posZ = -1
            return (posX, posY, posZ)
            
        if self._axis == 0:
            posY = self.x
            posZ = self.y
            posX = self._viewManager.slicePosition[0]
        elif self._axis == 1:
            posY = self._viewManager.slicePosition[1]
            posZ = self.y
            posX = self.x
        else:
            posY = self.y
            posZ = self._viewManager.slicePosition[2]
            posX = self.x
        return (posX, posY, posZ)
    
    #TODO oli
    def mouseMoveEvent(self,event):
        if self._dragMode == True:
            #the mouse was moved because the user wants to change
            #the viewport
            self._deltaPan = QPointF(event.pos() - self._lastPanPoint)
            self.panning()
            self._lastPanPoint = event.pos()
            return
        if self.ticker.isActive():
            #the view is still scrolling
            #do nothing until it comes to a complete stop
            return
        
        #the mouse was moved because the user is drawing
        #or he wants to otherwise interact with the data!
        self.mousePos = mousePos = self.mapToScene(event.pos())
        x = self.x = mousePos.x()
        y = self.y = mousePos.y()

        width, height = self._viewManager.imageShape(self._axis)
        valid = x > 0 and x < width and y > 0 and y < height                
        self.mouseMoved.emit(self._axis, x, y, valid)
                
        if self._isDrawing:
            line = self._drawManager.moveTo(mousePos)
            line.setZValue(99)
            self.tempImageItems.append(line)
            self.scene().addItem(line)

    def mouseDoubleClickEvent(self, event):
        mousePos = self.mapToScene(event.pos())
        self.mouseDoubleClicked.emit(self._axis, mousePos.x(), mousePos.y())

    #===========================================================================
    # Navigate in Volume
    #===========================================================================
    
    def sliceUp(self):
        self.changeSlice(1)
        
    def sliceUp10(self):
        self.changeSlice(10)

    def sliceDown(self):
        self.changeSlice(-1)

    def sliceDown10(self):
        self.changeSlice(-10)

    def changeSlice(self, delta):
        if self._isDrawing:
            self.endDrawing(self.mousePos)
            self._isDrawing = True
            self._drawManager.beginDrawing(self.mousePos, self.self.shape2D)
        
        self._viewManager.changeSliceDelta(self._axis, delta)
        InteractionLogger.log("%f: changeSliceDelta(axis, num) %d, %d" % (time.clock(), self._axis, delta))
        
    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def doScale(self, factor):
        self.factor = self.factor * factor
        InteractionLogger.log("%f: zoomFactor(factor) %f" % (time.clock(), self.factor))     
        self.scale(factor, factor)
        #FIXME
        self.scene()._imageSceneRenderer.renderImage(self.viewportRect(), self.porting_image, self.porting_overlays)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from overlaySlice import OverlaySlice 
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from testing import testVolume, AnnotatedImageData
        
    class ImageView2DTest(QApplication):    
        def __init__(self, args):
            app = QApplication.__init__(self, args)

            N = 1024
            self.data = (numpy.random.rand(2*N ,5, N)*255).astype(numpy.uint8)

            axis = 1
            
            viewManager = ViewManager(self.data)
            drawManager = DrawManager()
            
            self.ImageView2D = ImageView2D(axis, viewManager, drawManager)
            self.ImageView2D.drawingEnabled = True
            self.ImageView2D.mouseMoved.connect(lambda axis, x, y, valid: self.ImageView2D.crossHairCursor.showXYPosition(x,y))

            self.testChangeSlice(3, axis)
        
            self.ImageView2D.sliceChanged.connect(self.testChangeSlice)
            
            self.ImageView2D.show()
            

        def testChangeSlice(self, num, axis):
            s = 3*[slice(None,None,None)]
            s[axis] = num
            
            self.image = OverlaySlice(self.data[s], color = QColor("black"), alpha = 1, colorTable = None, min = None, max = None, autoAlphaChannel = True)
            self.overlays = [self.image]
            
            #FIMXE
            self.ImageView2D.porting_image = self.image
            self.ImageView2D.porting_overlays = self.overlays
            
            print "changeSlice num=%d, axis=%d" % (num, axis)

    app = ImageView2DTest([""])
    app.exec_()

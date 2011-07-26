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

from PyQt4.QtCore import QPoint, QPointF, QTimer, pyqtSignal, Qt, \
                         QString
from PyQt4.QtGui import QColor, QCursor, QGraphicsView, QPainter, QImage, \
                        QVBoxLayout, QApplication, QTransform
from PyQt4.QtOpenGL import QGLWidget

import numpy
import time

from drawManager import DrawManager
from crossHairCursor import CrossHairCursor
from sliceIntersectionMarker import SliceIntersectionMarker
from imageScene2D import ImageScene2D

from interactionLogger import InteractionLogger

#*******************************************************************************
# I m a g e V i e w 2 D                                                        *
#*******************************************************************************

class ImageView2D(QGraphicsView):
    #notifies about the relative change in the slicing position
    #that is requested
    changeSliceDelta   = pyqtSignal(int)
    
    drawing            = pyqtSignal(QPointF)
    beginDraw          = pyqtSignal(QPointF)
    endDraw            = pyqtSignal(QPointF)
    
    #notifies that the mouse has moved to 2D coordinate x,y
    mouseMoved         = pyqtSignal(int, int)
    #notifies that the user has double clicked on the 2D coordinate x,y    
    mouseDoubleClicked = pyqtSignal(int, int)
    
    drawUpdateInterval = 300 #ms
    
    @property
    def shape(self):
        return self._shape
    @shape.setter
    def shape(self, s):
        self._shape = s
        self.scene().shape                  = s
        self._crossHairCursor.shape         = s
        self._sliceIntersectionMarker.shape = s
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, n):
        self._name = n

    def _initializeGL(self):
        self.scene().initializeGL()
           
    @property
    def hud(self):
        return self._hud
    @hud.setter
    def hud(self, hud):
        '''Sets up a heads up display at the upper left corner of the view
        
        hud -- a QWidget
        '''
        
        self._hud = hud
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self._hud)
        self.layout().addStretch()


    @property
    def drawingEnabled(self):
        return self._drawingEnabled
    @drawingEnabled.setter
    def drawingEnabled(self, enable):
        self._drawingEnabled = enable 

    def __init__(self, drawManager, useGL=False):
        QGraphicsView.__init__(self)
        self._useGL = useGL
        
        #these attributes are exposed as public properties above
        self._shape  = None #2D shape of this view's shown image
        self._slices = None #number of slices that are stacked
        self._name   = ''
        self._hud    = None
        self._drawingEnabled = False
        
        self._crossHairCursor         = None
        self._sliceIntersectionMarker = None
        
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
        else:
            #Unfortunately, setting these flags has no effect when
            #Cache background is turned on.
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
        
        #Intitialize the scene
        self.setScene(ImageScene2D())
        if self._useGL:
            self.scene().activateOpenGL( self.openglWidget )

        #observe the scene, waiting for changes of the content
        self.scene().contentChanged.connect(self.onContentChange)
        if self._useGL:
            self._initializeGL()
        self._crossHairCursor = CrossHairCursor()
        self._crossHairCursor.setZValue(99)
        self.scene().addItem(self._crossHairCursor)
        
        self._sliceIntersectionMarker = SliceIntersectionMarker()
        self._sliceIntersectionMarker.setZValue(100)
        self.scene().addItem(self._sliceIntersectionMarker)
        #FIXME: Use a QAction here so that we do not have to synchronize
        #between this initial state and the toggle button's initial state
        self._sliceIntersectionMarker.setVisibility(True)
        
        #FIXME: MVC refactor 
        self._drawManager = drawManager
 
        #FIXME: this should be private, but is currently used from
        #       within the image scene renderer
        self.tempImageItems = []
        
        self._isDrawing = False
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

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tickerEvent)
        #label updates while drawing, needed for interactive segmentation
        self._drawTimer = QTimer(self)
        self._drawTimer.timeout.connect(self.notifyDrawing)
        
        # invisible cursor to enable custom cursor
        self._hiddenCursor = QCursor(Qt.BlankCursor)
        # For screen recording BlankCursor doesn't work
        #self.hiddenCursor = QCursor(Qt.ArrowCursor)
        

#FIXME: do we want to have these connects here or somewhere else?
#FIXME: resurrect
#        self._drawManager.brushSizeChanged.connect(self._crossHairCursor.setBrushSize)
#        self._drawManager.brushColorChanged.connect(self._crossHairCursor.setColor)
#        
#        self._crossHairCursor.setBrushSize(self._drawManager.brushSize)
#        self._crossHairCursor.setColor(self._drawManager.drawColor)

        self._tempErase = False
        
    def onContentChange(self):
        '''Observe the graphics scene, waiting for content changes.

        After a scene's content changed, it starts to render new tiles. This
        method prepares for these new tiles arriving little by little.
        '''
      #  if not self._useGL:
            #reset the background cache
            #self.resetCachedContent()
            #pass

    def swapAxes(self):          
        '''Displays this image as if the x and y axes were swapped.
        '''
        #FIXME: This is needed for the current arrangements of the three
        #       3D slice views. Can this be made more elegant
        self.rotate(90.0)
        self.scale(1.0,-1.0)
        
    def _cleanUp(self):        
        self._ticker.stop()
        self._drawTimer.stop()
        del self._drawTimer
        del self._ticker

    def viewportRect(self):
        return self.mapToScene(self.viewport().geometry()).boundingRect()

    def saveSlice(self, filename):
        #print "Saving in ", filename, "slice #", self.sliceNumber, "axis", self._axis
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
        print "ImageView2D.notifyDrawing"
        #FIXME: resurrect
        self.drawing.emit(self.mousePos)
    
    def beginDrawing(self, pos):
        InteractionLogger.log("%f: beginDrawing`()" % (time.clock()))   
        self.mousePos = pos
        self._isDrawing  = True
        line = self._drawManager.beginDrawing(pos, self.shape)
        line.setZValue(99)
        self.tempImageItems.append(line)
        self.scene().addItem(line)
        if self.drawUpdateInterval > 0:
            self._drawTimer.start(self.drawUpdateInterval) #update labels every some ms 
        self.beginDraw.emit(pos)
        
    def endDrawing(self, pos):
        InteractionLogger.log("%f: endDrawing()" % (time.clock()))     
        self._drawTimer.stop()
        self._isDrawing = False
        self.endDraw.emit(pos)

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor(Qt.SizeAllCursor))
            self._lastPanPoint = event.pos()
            self._crossHairCursor.setVisible(False)
            self._dragMode = True
            if self._ticker.isActive():
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
            if self._ticker.isActive():
                return
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self._drawManager.setErasing()
                self._tempErase = True
            mousePos = self.mapToScene(event.pos())
            self.beginDrawing(mousePos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor())
            releasePoint = event.pos()
            self._lastPanPoint = releasePoint
            self._dragMode = False
            self._ticker.start(20)
        if self._isDrawing:
            mousePos = self.mapToScene(event.pos())
            self.endDrawing(mousePos)
        if self._tempErase:
            self._drawManager.disableErasing()
            self._tempErase = False

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
    
    def mouseMoveEvent(self,event):
        if self._dragMode == True:
            #the mouse was moved because the user wants to change
            #the viewport
            self._deltaPan = QPointF(event.pos() - self._lastPanPoint)
            self._panning()
            self._lastPanPoint = event.pos()
            return
        if self._ticker.isActive():
            #the view is still scrolling
            #do nothing until it comes to a complete stop
            return
        
        self.mousePos = mousePos = self.mapToScene(event.pos())
        x = self.x = mousePos.x()
        y = self.y = mousePos.y()
             
        self.mouseMoved.emit(x, y)
                
        if self._isDrawing:
            line = self._drawManager.moveTo(mousePos)
            line.setZValue(99)
            self.tempImageItems.append(line)
            self.scene().addItem(line)

    def mouseDoubleClickEvent(self, event):
        mousePos = self.mapToScene(event.pos())
        self.mouseDoubleClicked.emit(mousePos.x(), mousePos.y())

    def changeSlice(self, delta):
        if self._isDrawing:
            self.endDrawing(self.mousePos)
            self._isDrawing = True
            self._drawManager.beginDrawing(self.mousePos, self.self.shape2D)
        
        self.changeSliceDelta.emit(delta)
        
        #FIXME resurrect
        #InteractionLogger.log("%f: changeSliceDelta(axis, num) %d, %d" % (time.clock(), self._axis, delta))
        
    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)
        
    def changeViewPort(self,qRectf):
        self.fitInView(qRectf,mode = Qt.KeepAspectRatio)

    def doScale(self, factor):
        self._zoomFactor = self._zoomFactor * factor
        InteractionLogger.log("%f: zoomFactor(factor) %f" % (time.clock(), self._zoomFactor))     
        self.scale(factor, factor)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************
if __name__ == '__main__':
    from overlaySlice import OverlaySlice 
    import sys
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QMainWindow
    from scipy.misc import lena
    
    def checkerboard(shape, squareSize):
        cb = numpy.zeros(shape)
        for i in range(shape[0]/squareSize):
            for j in range(shape[1]/squareSize):
                a = i*squareSize
                b = min((i+1)*squareSize, shape[0])
                c = j*squareSize
                d = min((j+1)*squareSize, shape[1])
                if i%2 == j%2:
                    cb[a:b,c:d] = 255
        return cb
    
    def cross(shape, width):
        c = numpy.zeros(shape)
        w2 = shape[0]/2
        h2 = shape[1]/2
        c[0:shape[0], h2-width/2:h2+width/2] = 255
        c[w2-width/2:w2+width/2, 0:shape[1]] = 255
        return c
    
    class ImageView2DTest(QMainWindow):    
        def __init__(self, useGL):
            QMainWindow.__init__(self)
            
            self.lena = lena().swapaxes(0,1)
            self.checkerboard = checkerboard(self.lena.shape, 20)
            self.cross = cross(self.lena.shape, 30)

            drawManager = DrawManager()
            self.imageView2D = ImageView2D(drawManager, useGL=useGL)
            self.imageView2D.drawingEnabled = True
            self.imageView2D.name = 'ImageView2D:'
            self.imageView2D.shape = self.lena.shape
            self.imageView2D.slices = 1
            self.setCentralWidget(self.imageView2D)

            imageSlice = OverlaySlice(self.lena, color = QColor("red"), alpha = 1.0, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            cbSlice    = OverlaySlice(self.checkerboard, color = QColor("green"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            crossSlice = OverlaySlice(self.cross, color = QColor("blue"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            
            self.imageView2D.scene().setContent(self.imageView2D.viewportRect(), None, (imageSlice, cbSlice, crossSlice))

    if not 'gl' in sys.argv and not 's' in sys.argv:
        print "Usage: python imageView2D.py mode"
        print "  mode = 's' software rendering"
        print "  mode = 'gl OpenGL rendering'"
        sys.exit(0)
         
    app = QApplication(sys.argv)
    i = ImageView2DTest('gl' in sys.argv)
    i.show()
    app.exec_()

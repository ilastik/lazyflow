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
from PyQt4.QtGui import QCursor, QGraphicsView, QPainter, QImage, \
                        QVBoxLayout, QApplication, QTransform

import numpy

from crossHairCursor import CrossHairCursor
from sliceIntersectionMarker import SliceIntersectionMarker

#*******************************************************************************
# I m a g e V i e w 2 D                                                        *
#*******************************************************************************

class ImageView2D(QGraphicsView):
    """
    Shows a ImageScene2D to the user and allows for interactive
    scrolling, panning, zooming etc. It intercepts all meaningful
    events on the widget for further interpretation (e.g. the view
    does not know which slicing axis it represents in the 3D slice
    viewer setting).
    """
    
    #notifies about the relative change in the slicing position
    #that is requested
    changeSliceDelta   = pyqtSignal(int)
    
    #all the following signals refer to data coordinates
    drawing            = pyqtSignal(QPointF)
    beginDraw          = pyqtSignal(QPointF, object)
    endDraw            = pyqtSignal(QPointF)
    
    erasingToggled     = pyqtSignal(bool)            
    
    #notifies that the mouse has moved to 2D data coordinate x,y
    mouseMoved         = pyqtSignal(int, int)
    #notifies that the user has double clicked on the 2D data coordinate x,y    
    mouseDoubleClicked = pyqtSignal(int, int)
    
    drawUpdateInterval = 300 #ms
    
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
        self.scene().sceneShape             = sceneShape
        self._crossHairCursor.shape         = sceneShape
        self._sliceIntersectionMarker.shape = sceneShape
    
    #FIXME unused?
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, n):
        self._name = n
           
    @property
    def hud(self):
        return self._hud
    @hud.setter
    def hud(self, hud):
        """
        Sets up a heads up display at the upper left corner of the view
        
        hud -- a QWidget
        """
        
        self._hud = hud
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addLayout(self._hud)
        self.layout().addStretch()


    @property
    def drawingEnabled(self):
        return self._drawingEnabled
    @drawingEnabled.setter
    def drawingEnabled(self, enable):
        self._drawingEnabled = enable 
    
    def __init__(self, imagescene2d):
        """
        Constructs a view upon a ImageScene2D
        
        imagescene2d -- a ImgeScene2D instance
        """
        
        QGraphicsView.__init__(self)
        self.setScene(imagescene2d)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        #these attributes are exposed as public properties above
        self._sliceShape  = None #2D shape of this view's shown image
        self._slices = None #number of slices that are stacked
        self._name   = ''
        self._hud    = None
        self._drawingEnabled = False
        
        self._crossHairCursor         = None
        self._sliceIntersectionMarker = None
        
        #
        # Setup the Viewport for fast painting
        #
        
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

        self._crossHairCursor = CrossHairCursor(self.scene())
        self._crossHairCursor.setZValue(99)
        
        self._sliceIntersectionMarker = SliceIntersectionMarker()
        self._sliceIntersectionMarker.setZValue(100)
        self.scene().addItem(self._sliceIntersectionMarker)
        #FIXME: Use a QAction here so that we do not have to synchronize
        #between this initial state and the toggle button's initial state
        self._sliceIntersectionMarker.setVisibility(True)
 
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

        self._tempErase = False
        
    def _cleanUp(self):        
        self._ticker.stop()
        self._drawTimer.stop()
        del self._drawTimer
        del self._ticker

    def viewportRect(self):
        """
        Return a QRectF giving the part of the scene currently displayed in this
        widget's viewport in the scene's coordinates
        """
        return self.mapToScene(self.viewport().geometry()).boundingRect()
   
    def mapScene2Data(self, pos):
        return self.scene().scene2data.map(pos)
   
    def notifyDrawing(self):
        print "ImageView2D.notifyDrawing"
        #FIXME: resurrect
        self.drawing.emit(self.mousePos)
    
    def beginDrawing(self, pos):
        self.mousePos = pos
        self._isDrawing  = True
        self.beginDraw.emit(pos, self.sliceShape)
        
    def endDrawing(self, pos): 
        self._drawTimer.stop()
        self._isDrawing = False
        self.endDraw.emit(pos)

    def wheelEvent(self, event):
        keys = QApplication.keyboardModifiers()
        k_alt = (keys == Qt.AltModifier)
        k_ctrl = (keys == Qt.ControlModifier)

        self.mousePos = self.mapScene2Data(self.mapToScene(event.pos()))

        sceneMousePos = self.mapToScene(event.pos())
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
            offset = sceneMousePos - mousePosAfterScale
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
                self.erasingToggled.emit(True)
                self._tempErase = True
            self.mousePos = self.mapScene2Data(self.mapToScene(event.pos()))
            self.beginDrawing(self.mousePos)
            
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
        
        self.mousePos = mousePos = self.mapScene2Data(self.mapToScene(event.pos()))
        oldX, oldY = self.x, self.y
        x = self.x = mousePos.x()
        y = self.y = mousePos.y()
        self.mouseMoved.emit(x,y)

        if self._isDrawing:
            ### FIXME
            patch = None
            patchNr = -1
            for patchNr, patch in enumerate(self.scene().imagePatches):
                patch = patch[self.scene()._numLayers+1]
                if patch.rectF.contains(self.mapToScene(event.pos())):
                    break
            patch.mutex.lock()
            p = QPainter(patch.image)
            p.setPen(self.scene()._brush)
            
            tL = patch.rectF.topLeft()
            o  = self.scene().data2scene.map(QPointF(oldX,oldY))
            n  = self.scene().data2scene.map(QPointF(x,y))
            
            p.drawLine(o-tL, n-tL)
            p.end()
            patch.dirty = True
            patch.mutex.unlock()
            self.scene()._schedulePatchRedraw(patchNr)
            ### end FIXME
            
            self.drawing.emit(mousePos)

    def mouseReleaseEvent(self, event):
        self.mousePos = self.mapScene2Data(self.mapToScene(event.pos()))
        
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor())
            releasePoint = event.pos()
            self._lastPanPoint = releasePoint
            self._dragMode = False
            self._ticker.start(20)
        if self._isDrawing:
            self.endDrawing(self.mousePos)
        if self._tempErase:
            self.erasingToggled.emit(False)
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
    
    def mouseDoubleClickEvent(self, event):
        self.mousePos = self.mapScene2Data(self.mapToScene(event.pos()))
        self.mouseDoubleClicked.emit(self.mousePos.x(), self.mousePos.y())

    def changeSlice(self, delta):       
        if self._isDrawing:
            self.endDrawing(self.mousePos)
            self._isDrawing = True
            
            #FIXME:
            #self._drawManager.beginDrawing(self.mousePos, self.self.shape2D)
        
        self.changeSliceDelta.emit(delta)
        
    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)
        
    def changeViewPort(self,qRectf):
        self.fitInView(qRectf,mode = Qt.KeepAspectRatio)

    def doScale(self, factor):
        self._zoomFactor = self._zoomFactor * factor
        self.scale(factor, factor)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************
if __name__ == '__main__':
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
        def __init__(self):
            assert False, "I'm broken. Please fixme."
            QMainWindow.__init__(self)
            
            self.lena = lena().swapaxes(0,1)
            self.checkerboard = checkerboard(self.lena.shape, 20)
            self.cross = cross(self.lena.shape, 30)

            self.imageView2D = ImageView2D()
            self.imageView2D.drawingEnabled = True
            self.imageView2D.name = 'ImageView2D:'
            self.imageView2D.shape = self.lena.shape
            self.imageView2D.slices = 1
            self.setCentralWidget(self.imageView2D)

            #imageSlice = OverlaySlice(self.lena, color = QColor("red"), alpha = 1.0, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            #cbSlice    = OverlaySlice(self.checkerboard, color = QColor("green"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            #crossSlice = OverlaySlice(self.cross, color = QColor("blue"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            
            self.imageView2D.scene().setContent(self.imageView2D.viewportRect(), None, (imageSlice, cbSlice, crossSlice))
         
    app = QApplication(sys.argv)
    i = ImageView2DTest()
    i.show()
    app.exec_()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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
                         QSize
from PyQt4.QtOpenGL import QGLWidget, QGLFramebufferObject
from PyQt4.QtGui import *

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy
import os.path, time
import sip

from ilastik.gui.iconMgr import ilastikIcons
from patchAccessor import PatchAccessor
from viewManager import ViewManager
from drawManager import DrawManager

from imagescenerenderer import ImageSceneRenderer
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
# I m a g e S c e n e                                                          *
#*******************************************************************************
#TODO: ImageScene should not care/know about what axis it is!
class ImageScene(QGraphicsView):
    sliceChanged       = pyqtSignal(int,int)
    drawing            = pyqtSignal(int, QPointF)
    beginDraw          = pyqtSignal(int, QPointF)
    endDraw            = pyqtSignal(int, QPointF)
    mouseMoved         = pyqtSignal(int, int, int, bool)
    mouseDoubleClicked = pyqtSignal(int, int, int)
    
    axisColor = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]
        
    def __init__(self, axis, viewManager, drawManager, sharedOpenGLWidget = None):
        """
        imShape: 3D shape of the block that this slice view displays.
                 first two entries denote the x,y extent of one slice,
                 the last entry is the extent in slice direction
        """
        QGraphicsView.__init__(self)
        self.scene = CustomGraphicsScene(sharedOpenGLWidget)
        
        assert(axis in [0,1,2])
        
        self.drawManager = drawManager
        self.viewManager = viewManager
        
        self.tempImageItems = []
        self.axis = axis
        self.sliceNumber = 0
        self.sliceExtent = viewManager.imageExtent(axis)
        self.isDrawing = False
        self.view = self
        self.image = QImage(QSize(*viewManager.imageShape(axis)), QImage.Format_ARGB32)
        self.scene.image = self.image
        self.border = None
        self.allBorder = None
        self.factor = 1.0
        
        #for panning
        self.lastPanPoint = QPoint()
        self.dragMode = False
        self.deltaPan = QPointF(0,0)
        
        self.drawingEnabled = False
        
        self.openglWidget = None
        self.sharedOpenGLWidget = sharedOpenGLWidget
        
        self.fastRepaint = True
        self.drawUpdateInterval = 300

        if self.sliceExtent > 1:
            self.setLayout(QVBoxLayout())
            self.layout().setContentsMargins(0,0,0,0)

            axisLabels = ["X:", "Y:", "Z:"]
            self.hud = Hud(0, self.sliceExtent - 1, axisLabels[self.axis])

            self.layout().addWidget(self.hud)
            self.layout().addStretch()
        
        self.patchAccessor = PatchAccessor(*viewManager.imageShape(axis),blockSize=64)
        
        if self.scene.useGL:
            self.openglWidget = QGLWidget(shareWidget = sharedOpenGLWidget)
            self.setViewport(self.openglWidget)
            self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            
            self.openglWidget.context().makeCurrent()
            self.scene.tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D,self.scene.tex)
            #print "generating OpenGL texture of size %d x %d" % (self.scene.image.width(), self.scene.image.height())
            glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, viewManager.imageShape(axis)[0], viewManager.imageShape(axis)[1], \
                         0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.image.bits().__int__()))

            self.imagePatches = range(self.patchAccessor.patchCount)
            for i, p in enumerate(self.imagePatches):
                b = self.patchAccessor.getPatchBounds(i, 0)
                self.imagePatches[i] = QImage(b[1]-b[0], b[3] -b[2], QImage.Format_RGB888)
            
        self.view.setScene(self.scene)
        self.scene.setSceneRect(0,0, *viewManager.imageShape(axis))
        self.view.setSceneRect(0,0, *viewManager.imageShape(axis))
        self.scene.bgColor = QColor(Qt.white)
        if os.path.isfile('gui/backGroundBrush.png'):
            self.scene.bgBrush = QBrush(QImage('gui/backGroundBrush.png'))
        else:
            self.scene.bgBrush = QBrush(QColor(Qt.black))

        self.view.setRenderHint(QPainter.Antialiasing, False)
        #self.view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        
        #Unfortunately, setting the style like this make the scroll bars look
        #really crappy...
        #self.setStyleSheet("QWidget:!focus { border: 2px solid " + self.axisColor[self.axis].name() +"; border-radius: 4px; }\
        #                    QWidget:focus { border: 2px solid white; border-radius: 4px; }")

        if self.axis is 0:
            self.view.rotate(90.0)
            self.view.scale(1.0,-1.0)

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
        allBorderPath.addRect(0, 0, *viewManager.imageShape(axis))
        self.allBorder = QGraphicsPathItem(allBorderPath)
        self.allBorder.setBrush(brush)
        self.allBorder.setPen(QPen(Qt.NoPen))
        self.scene.addItem(self.allBorder)
        self.allBorder.setVisible(False)
        self.allBorder.setZValue(99)

        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self.tickerEvent)
        #label updates while drawing, needed for interactive segmentation
        self.drawTimer = QTimer(self)
        self.drawTimer.timeout.connect(self.notifyDrawing)
        
        # invisible cursor to enable custom cursor
        self.hiddenCursor = QCursor(Qt.BlankCursor)
        
        # For screen recording BlankCursor dont work
        #self.hiddenCursor = QCursor(Qt.ArrowCursor)
        
        #self.connect(self, SIGNAL("destroyed()"), self.cleanUp)

        self.crossHairCursor = CrossHairCursor(self.image.width(), self.image.height())
        self.crossHairCursor.setZValue(100)
        self.scene.addItem(self.crossHairCursor)
        
        self.drawManager.brushSizeChanged.connect(self.crossHairCursor.setBrushSize)
        self.crossHairCursor.setBrushSize(self.drawManager.brushSize)

        self.sliceIntersectionMarker = SliceIntersectionMarker(self.image.width(), self.image.height())
        if self.axis == 0:
            self.sliceIntersectionMarker.setColor(self.axisColor[1], self.axisColor[2])
        elif self.axis == 1:
            self.sliceIntersectionMarker.setColor(self.axisColor[0], self.axisColor[2])
        elif self.axis == 2:
            self.sliceIntersectionMarker.setColor(self.axisColor[0], self.axisColor[1])    
        self.scene.addItem(self.sliceIntersectionMarker)

        self.tempErase = False
        
        self.imageSceneRenderer = ImageSceneRenderer(self)
        self.imageSceneRenderer.updatesAvailable.connect(self.viewport().repaint)
        
    def setBorderMarginIndicator(self, margin):
        """
        update the border margin indicator (left, right, top, bottom)
        to reflect the new given margin
        """
        
        imShape = self.viewManager.imageShape(self.axis)
        
        self.margin = margin
        if self.border:
            self.scene.removeItem(self.border)
        borderPath = QPainterPath()
        borderPath.setFillRule(Qt.WindingFill)
        borderPath.addRect(0,0, margin, imShape[1])
        borderPath.addRect(0,0, imShape[0], margin)
        borderPath.addRect(imShape[0]-margin,0, margin, imShape[1])
        borderPath.addRect(0,imShape[1]-margin, imShape[0], margin)
        self.border = QGraphicsPathItem(borderPath)
        brush = QBrush(QColor(0,0,255))
        brush.setStyle( Qt.Dense7Pattern )
        self.border.setBrush(brush)
        self.border.setPen(QPen(Qt.NoPen))
        self.border.setZValue(200)
        self.scene.addItem(self.border)

    def setSliceIntersection(self, state):
        self.sliceIntersectionMarker.setVisibility(state)
            
    def updateSliceIntersection(self, num, axis):
        #print "updateSliceIntersection(%d, %d)" % (num, axis)
        if self.axis == 0:
            if axis == 1:
                self.sliceIntersectionMarker.setPositionX(num)
            elif axis == 2:
                self.sliceIntersectionMarker.setPositionY(num)
            else:
                return
        elif self.axis == 1:
            if axis == 0:
                self.sliceIntersectionMarker.setPositionX(num)
            elif axis == 2:
                self.sliceIntersectionMarker.setPositionY(num)
            else:
                return
        elif self.axis == 2:
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

    def displayNewSlice(self, image, overlays = (), fastPreview = True, normalizeData = False):
        #if, in slicing direction, we are within the margin of the image border
        #we set the border overlay indicator to visible
        allBorder = (self.sliceNumber < self.margin or\
                     self.sliceExtent - self.sliceNumber < self.margin) \
                     and self.sliceExtent > 1
        self.allBorder.setVisible(allBorder)
        self.imageSceneRenderer.renderImage(image, overlays)
        
    def saveSlice(self, filename):
        print "Saving in ", filename, "slice #", self.sliceNumber, "axis", self.axis
        result_image = QImage(self.scene.image.size(), self.scene.image.format())
        p = QPainter(result_image)
        for patchNr in range(self.patchAccessor.patchCount):
            bounds = self.patchAccessor.getPatchBounds(patchNr)
            if self.openglWidget is None:
                p.drawImage(0, 0, self.scene.image)
            else:
                p.drawImage(bounds[0], bounds[2], self.imagePatches[patchNr])
        p.end()
        #horrible way to transpose an image. but it works.
        transform = QTransform()
        transform.rotate(90)
        result_image = result_image.mirrored()
        result_image = result_image.transformed(transform)
        result_image.save(QString(filename))

    def display(self, image, overlays = ()):
        self.thread.queue.clear()
        self.updatePatches(range(self.patchAccessor.patchCount),image, overlays)
    
    def notifyDrawing(self):
        self.drawing.emit(self.axis, self.mousePos)
    
    def beginDrawing(self, pos):
        imShape = self.viewManager.imageShape(self.axis)
        
        InteractionLogger.log("%f: beginDrawing`()" % (time.clock()))   
        self.mousePos = pos
        self.isDrawing  = True
        line = self.drawManager.beginDrawing(pos, imShape)
        line.setZValue(99)
        self.tempImageItems.append(line)
        self.scene.addItem(line)
        if self.drawUpdateInterval > 0:
            self.drawTimer.start(self.drawUpdateInterval) #update labels every some ms
            
        self.beginDraw.emit(self.axis, pos)
        
    def endDrawing(self, pos):
        InteractionLogger.log("%f: endDrawing()" % (time.clock()))     
        self.drawTimer.stop()
        self.isDrawing = False
        
        self.endDraw.emit(self.axis, pos)

    def wheelEvent(self, event):
        keys = QApplication.keyboardModifiers()
        k_alt = (keys == Qt.AltModifier)
        k_ctrl = (keys == Qt.ControlModifier)

        self.mousePos = self.mapToScene(event.pos())
        grviewCenter  = self.mapToScene(self.viewport().rect().center())

        if event.delta() > 0:
            if k_alt is True:
                self.changeSlice(10)
            elif k_ctrl is True:
                scaleFactor = 1.1
                self.doScale(scaleFactor)
            else:
                self.changeSlice(1)
        else:
            if k_alt is True:
                self.changeSlice(-10)
            elif k_ctrl is True:
                scaleFactor = 0.9
                self.doScale(scaleFactor)
            else:
                self.changeSlice(-1)
        if k_ctrl is True:
            mousePosAfterScale = self.mapToScene(event.pos())
            offset = self.mousePos - mousePosAfterScale
            newGrviewCenter = grviewCenter + offset
            self.centerOn(newGrviewCenter)
            self.mouseMoveEvent(event)



#FIXME uncommented to get rid of dependencies to volumeEditor
#    def tabletEvent(self, event):
#        self.setFocus(True)
#        
#        if not self.volumeEditor.labelWidget.currentItem():
#            return
#        
#        self.mousePos = mousePos = self.mapToScene(event.pos())
#        
#        if event.pointerType() == QTabletEvent.Eraser or QApplication.keyboardModifiers() == Qt.ShiftModifier:
#            self.drawManager.setErasing()
#        elif event.pointerType() == QTabletEvent.Pen and QApplication.keyboardModifiers() != Qt.ShiftModifier:
#            self.drawManager.disableErasing()
#        if self.isDrawing == True:
#            if event.pressure() == 0:
#                self.endDrawing(mousePos)
#                self.volumeEditor.changeSlice(self.volumeEditor.viewManager.slicePosition[self.axis], self.axis)
#            else:
#                if self.drawManager.erasing:
#                    #make the brush size bigger while erasing
#                    self.drawManager.setBrushSize(int(event.pressure()*10))
#                else:
#                    self.drawManager.setBrushSize(int(event.pressure()*7))
#        if self.isDrawing == False:
#            if event.pressure() > 0:
#                self.beginDrawing(mousePos)
#                
#        self.mouseMoveEvent(event)

    #TODO oli
    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor(Qt.SizeAllCursor))
            self.lastPanPoint = event.pos()
            self.crossHairCursor.setVisible(False)
            self.dragMode = True
            if self.ticker.isActive():
                self.deltaPan = QPointF(0, 0)

        if event.buttons() == Qt.RightButton:
            #make sure that we have the cursor at the correct position
            #before we call the context menu
            self.mouseMoveEvent(event)
            self.customContextMenuRequested.emit(event.pos())
            return

        if not self.drawingEnabled:
            print "ImageScene.mousePressEvent: drawing is not enabled"
            return
        
        if event.buttons() == Qt.LeftButton:
            #don't draw if flicker the view
            if self.ticker.isActive():
                return
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.drawManager.setErasing()
                self.tempErase = True
            mousePos = self.mapToScene(event.pos())
            self.beginDrawing(mousePos)
            
    #TODO oli
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setCursor(QCursor())
            releasePoint = event.pos()
            
            self.lastPanPoint = releasePoint
            self.dragMode = False
            self.ticker.start(20)
        if self.isDrawing == True:
            mousePos = self.mapToScene(event.pos())
            self.endDrawing(mousePos)
        if self.tempErase == True:
            self.drawManager.disableErasing()
            self.tempErase = False

    #TODO oli
    def panning(self):
        hBar = self.horizontalScrollBar()
        vBar = self.verticalScrollBar()
        vBar.setValue(vBar.value() - self.deltaPan.y())
        if self.isRightToLeft():
            hBar.setValue(hBar.value() + self.deltaPan.x())
        else:
            hBar.setValue(hBar.value() - self.deltaPan.x())
        
        
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

    #TODO oli
    def qBound(self, minVal, current, maxVal):
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
        if self.deltaPan.x() == 0.0 and self.deltaPan.y() == 0.0 or self.dragMode == True:
            self.ticker.stop()
            cursor = QCursor()
            mousePos = self.mapToScene(self.mapFromGlobal(cursor.pos()))
            x = mousePos.x()
            y = mousePos.y()
            self.crossHairCursor.showXYPosition(x, y)
        else:
            self.deltaPan = self.deaccelerate(self.deltaPan)
            self.panning()
    
    def coordinateUnderCursor(self):
        """returns the coordinate that is defined by hovering with the mouse
           over one of the slice views. It is _not_ the coordinate as defined
           by the three slice views"""
        validArea = self.x > 0 and self.x < self.image.width() and self.y > 0 and self.y < self.image.height()
        if not validArea:
            posX = posY = posZ = -1
            return (posX, posY, posZ)
            
        if self.axis == 0:
            posY = self.x
            posZ = self.y
            posX = self.viewManager.slicePosition[0]
        elif self.axis == 1:
            posY = self.viewManager.slicePosition[1]
            posZ = self.y
            posX = self.x
        else:
            posY = self.y
            posZ = self.viewManager.slicePosition[2]
            posX = self.x
        return (posX, posY, posZ)
    
    #TODO oli
    def mouseMoveEvent(self,event):
        if self.dragMode == True:
            #the mouse was moved because the user wants to change
            #the viewport
            self.deltaPan = QPointF(event.pos() - self.lastPanPoint)
            self.panning()
            self.lastPanPoint = event.pos()
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

        valid = x > 0 and x < self.image.width() and y > 0 and y < self.image.height()                
        self.mouseMoved.emit(self.axis, x, y, valid)
                
        if self.isDrawing:
            line = self.drawManager.moveTo(mousePos)
            line.setZValue(99)
            self.tempImageItems.append(line)
            self.scene.addItem(line)

    def mouseDoubleClickEvent(self, event):
        mousePos = self.mapToScene(event.pos())
        self.mouseDoubleClicked.emit(self.axis, mousePos.x(), mousePos.y())

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
        if self.isDrawing:
            self.endDrawing(self.mousePos)
            self.isDrawing = True
            self.drawManager.beginDrawing(self.mousePos, self.imShape)

        self.viewManager.changeSliceDelta(self.axis, delta)
        InteractionLogger.log("%f: changeSliceDelta(axis, num) %d, %d" % (time.clock(), self.axis, delta))
        
    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def doScale(self, factor):
        self.factor = self.factor * factor
        InteractionLogger.log("%f: zoomFactor(factor) %f" % (time.clock(), self.factor))     
        self.view.scale(factor, factor)
        
#*******************************************************************************
# C u s t o m G r a p h i c s S c e n e                                        *
#*******************************************************************************

class CustomGraphicsScene(QGraphicsScene):
    def __init__(self, glWidget):
        QGraphicsScene.__init__(self)
        self.glWidget = glWidget
        self.useGL = (glWidget != None)
        self.bgColor = QColor(Qt.green)
        
        self.image = None
        self.tex = -1

    def drawBackgroundSoftware(self, painter, rect):
        if not self.image:
            return
        painter.setClipRect(rect)
        painter.drawImage(0,0,self.image)

    def drawBackgroundGL(self, painter, rect):
        self.glWidget.context().makeCurrent()
            
        #glClearColor(self.bgColor.redF(),self.bgColor.greenF(),self.bgColor.blueF(),1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.tex <= -1:
            return

        #self.glWidget.drawTexture(QRectF(self.image.rect()),self.tex)
        d = painter.device()
        dc = sip.cast(d,QGLFramebufferObject)

        rect = QRectF(self.image.rect())
        tl = rect.topLeft()
        br = rect.bottomRight()
        
        #flip coordinates since the texture is flipped
        #this is due to qimage having another representation thatn OpenGL
        rect.setCoords(tl.x(),br.y(),br.x(),tl.y())
        
        #switch corrdinates if qt version is small
        painter.beginNativePainting()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        dc.drawTexture(rect,self.tex)
        painter.endNativePainting()

    def drawBackground(self, painter, rect):
        if self.useGL:
            self.drawBackgroundGL(painter, rect)
        else:
            self.drawBackgroundSoftware(painter, rect)

#*******************************************************************************
# C r o s s H a i r C u r s o r                                                *
#*******************************************************************************

class CrossHairCursor(QGraphicsItem) :
    modeYPosition  = 0
    modeXPosition  = 1
    modeXYPosition = 2
    
    def boundingRect(self):
        return QRectF(0,0, self.width, self.height)
    def __init__(self, width, height):
        QGraphicsItem.__init__(self)
        
        self.width = width
        self.height = height
        
        self.penDotted = QPen(Qt.red, 2, Qt.DotLine, Qt.RoundCap, Qt.RoundJoin)
        self.penDotted.setCosmetic(True)
        
        self.penSolid = QPen(Qt.red, 2)
        self.penSolid.setCosmetic(True)
        
        self.x = 0
        self.y = 0
        self.brushSize = 0
        
        self.mode = self.modeXYPosition
    
    def setColor(self, color):
        self.penDotted = QPen(color, 2, Qt.DotLine, Qt.RoundCap, Qt.RoundJoin)
        self.penDotted.setCosmetic(True)
        self.penSolid  = QPen(color, 2)
        self.penSolid.setCosmetic(True)
        self.update()
    
    def showXPosition(self, x, y):
        """only mark the x position by displaying a line f(y) = x"""
        self.setVisible(True)
        self.mode = self.modeXPosition
        self.setPos(x, y - int(y))
        
    def showYPosition(self, y, x):
        """only mark the y position by displaying a line f(x) = y"""
        self.setVisible(True)
        self.mode = self.modeYPosition
        self.setPos(x - int(x), y)
        
    def showXYPosition(self, x,y):
        """mark the (x,y) position by displaying a cross hair cursor
           including a circle indicating the current brush size"""
        self.setVisible(True)
        self.mode = self.modeXYPosition
        self.setPos(x,y)
    
    def paint(self, painter, option, widget=None):
        painter.setPen(self.penDotted)
        
        if self.mode == self.modeXPosition:
            painter.drawLine(QPointF(self.x+0.5, 0), QPointF(self.x+0.5, self.height))
        elif self.mode == self.modeYPosition:
            painter.drawLine(QPointF(0, self.y), QPointF(self.width, self.y))
        else:
            painter.drawLine(QPointF(self.x -0.5*self.brushSize -3 ,self.y), QPointF(self.x -0.5*self.brushSize, self.y))
            painter.drawLine(QPointF(self.x+0.5*self.brushSize, self.y), QPointF(self.x+0.5*self.brushSize +3, self.y))

            painter.drawLine(QPointF(self.x, self.y-0.5*self.brushSize - 3), QPointF(self.x, self.y-0.5*self.brushSize))
            painter.drawLine(QPointF(self.x, self.y+0.5*self.brushSize), QPointF(self.x, self.y+0.5*self.brushSize + 3))

            painter.setPen(self.penSolid)
            painter.drawEllipse(QPointF(self.x, self.y), 0.5*self.brushSize, 0.5*self.brushSize)
        
    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.update()
        
    def setBrushSize(self, size):
        self.brushSize = size
        self.update()

#*******************************************************************************
# S l i c e I n t e r s e c t i o n M a r k e r                                *
#*******************************************************************************

class SliceIntersectionMarker(QGraphicsItem) :
    
    def boundingRect(self):
        return QRectF(0,0, self.width, self.height)
    
    def __init__(self, width, height):
        QGraphicsItem.__init__(self)
        
        self.width = width
        self.height = height
              
        self.penX = QPen(Qt.red, 2)
        self.penX.setCosmetic(True)
        
        self.penY = QPen(Qt.green, 2)
        self.penY.setCosmetic(True)
        
        self.x = 0
        self.y = 0
        
        self.isVisible = False

    def setPosition(self, x, y):
        self.x = x
        self.y = y
        self.update()
        
    def setPositionX(self, x):
        self.setPosition(x, self.y)
        
    def setPositionY(self, y):
        self.setPosition(self.x, y)  
   
    def setColor(self, colorX, colorY):
        self.penX = QPen(colorX, 2)
        self.penX.setCosmetic(True)
        self.penY = QPen(colorY, 2)
        self.penY.setCosmetic(True)
        self.update()
        
    def setVisibility(self, state):
        if state == True:
            self.isVisible = True
        else:
            self.isVisible = False
        self.update()
    
    def paint(self, painter, option, widget=None):
        if self.isVisible:
            painter.setPen(self.penY)
            painter.drawLine(QPointF(0.0,self.y), QPointF(self.width, self.y))
            
            painter.setPen(self.penX)
            painter.drawLine(QPointF(self.x, 0), QPointF(self.x, self.height))


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from ilastik.core.overlayMgr import OverlaySlice 
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from testing import testVolume, AnnotatedImageData
        
    class ImageSceneTest(QApplication):    
        def __init__(self, args):
            app = QApplication.__init__(self, args)

            self.data = testVolume(40)
            axis = 1
            
            viewManager = ViewManager(self.data)
            drawManager = DrawManager()
            
            self.imageScene = ImageScene(axis, viewManager, drawManager)
            self.imageScene.drawingEnabled = True
            
            self.testChangeSlice(20, axis)
        
            self.imageScene.sliceChanged.connect(self.testChangeSlice)
            
            self.imageScene.show()
            

        def testChangeSlice(self, num, axis):
            s = 3*[slice(None,None,None)]
            s[axis] = num
            
            self.image = OverlaySlice(self.data[s], color = QColor("black"), alpha = 1, colorTable = None, min = None, max = None, autoAlphaChannel = True)
            self.overlays = [self.image]
            
            self.imageScene.displayNewSlice(self.image, self.overlays, fastPreview = True, normalizeData = False)
            print "changeSlice num=%d, axis=%d" % (num, axis)

    app = ImageSceneTest([""])
    app.exec_()




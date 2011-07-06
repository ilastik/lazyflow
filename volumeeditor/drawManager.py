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

from PyQt4.QtCore import pyqtSignal, QObject, QThread, Qt, QSize, QPointF, QRectF, \
                         QRect, QPoint
from PyQt4.QtGui  import QWidget, QPen, QGraphicsScene, QColor, QGraphicsLineItem, \
                         QImage, QPainter, QGraphicsLineItem

import numpy
import threading
import time

#*******************************************************************************
# D r a w M a n a g e r                                                        *
#*******************************************************************************

class DrawManager(QObject):
    brushSizeChanged  = pyqtSignal(int)
    brushColorChanged = pyqtSignal(QColor)
    
    minBrushSize       = 1
    maxBrushSize       = 61
    defaultBrushSize   = 3
    defaultDrawnNumber = 1
    defaultColor       = Qt.white
    erasingColor       = Qt.black
    
    def __init__(self):
        QObject.__init__(self)
        self.shape = None
        self.bb    = QRect() #bounding box enclosing the drawing
        self.brushSize = self.defaultBrushSize
        self.drawColor = self.defaultColor
        self.drawnNumber = self.defaultDrawnNumber

        self.penVis  = QPen(self.drawColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.penDraw = QPen(self.drawColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.pos = None
        self.erasing = False
        
        #on which OverlayItem do we want to draw when self.drawingEnabled?
        self.drawOnto = None
        
        #an empty scene, where we add all drawn line segments
        #a QGraphicsLineItem, and which we can use to then
        #render to an image
        self.scene = QGraphicsScene()

    def copy(self):
        """
        make a shallow copy of DrawManager - needed for python 2.5 compatibility
        """
        cp = DrawManager()
        cp.shape = self.shape
        cp.brushSize = self.brushSize
        cp.penVis = self.penVis
        cp.penDraw = self.penDraw
        cp.pos = self.pos
        cp.erasing = self.erasing
        cp.scene = self.scene
        cp.imageScenes = self.imageScenes
        cp.color = self.drawColor
        return cp

    def growBoundingBox(self):
        self.bb.setLeft(  max(0, self.bb.left()-self.brushSize-1))
        self.bb.setTop(   max(0, self.bb.top()-self.brushSize-1 ))
        self.bb.setRight( min(self.shape[0], self.bb.right()+self.brushSize+1))
        self.bb.setBottom(min(self.shape[1], self.bb.bottom()+self.brushSize+1))

    def toggleErase(self):
        self.erasing = not(self.erasing)

    def setErasing(self):
        self.erasing = True
        self.brushColorChanged.emit(self.erasingColor)
    
    def disableErasing(self):
        self.erasing = False
        self.brushColorChanged.emit(self.drawColor)

    def setBrushSize(self, size):
        self.brushSize = size
        self.penVis.setWidth(size)
        self.penDraw.setWidth(size)
        self.brushSizeChanged.emit(self.brushSize)
    
    def setDrawnNumber(self, num):
        self.drawnNumber = num
        self.drawnNumberChanged.emit(num)
        
    def getBrushSize(self):
        return self.brushSize
    
    def brushSmaller(self):
        b = self.brushSize
        if b > self.minBrushSize:
            self.setBrushSize(b-1)
        
    def brushBigger(self):
        b = self.brushSize
        if self.brushSize < self.maxBrushSize:
            self.setBrushSize(b+1)
        
    def setBrushColor(self, color):
        self.drawColor = color
        self.penVis.setColor(color)
        self.emit.brushColorChanged(self.drawColor)
        
    def beginDrawing(self, pos, shape):
        self.shape = shape
        self.bb = QRectF(0, 0, self.shape[0], self.shape[1])
        self.scene.clear()
        if self.erasing:
            self.penVis.setColor(self.erasingColor)
        else:
            self.penVis.setColor(self.drawColor)
        self.pos = QPointF(pos.x()+0.0001, pos.y()+0.0001)
        line = self.moveTo(pos)
        return line

    def endDrawing(self, pos):
        self.moveTo(pos)
        self.growBoundingBox()

        tempi = QImage(QSize(self.bb.width(), self.bb.height()), QImage.Format_ARGB32_Premultiplied) #TODO: format
        tempi.fill(0)
        painter = QPainter(tempi)
        
        self.scene.render(painter, QRectF(QPointF(0,0), self.bb.size()), self.bb)
        
        return (self.bb.left(), self.bb.top(), tempi) #TODO: hackish, probably return a class ??

    def dumpDraw(self, pos):
        res = self.endDrawing(pos)
        self.beginDrawing(pos, self.shape)
        return res

    def moveTo(self, pos):    
        lineVis = QGraphicsLineItem(self.pos.x(), self.pos.y(), pos.x(), pos.y())
        lineVis.setPen(self.penVis)
        
        line = QGraphicsLineItem(self.pos.x(), self.pos.y(), pos.x(), pos.y())
        line.setPen(self.penDraw)
        self.scene.addItem(line)

        self.pos = pos
        x = pos.x()
        y = pos.y()
        #update bounding Box :
        if x > self.bb.right():
            self.bb.setRight(x)
        if x < self.bb.left():
            self.bb.setLeft(x)
        if y > self.bb.bottom():
            self.bb.setBottom(y)
        if y < self.bb.top():
            self.bb.setTop(y)
        return lineVis

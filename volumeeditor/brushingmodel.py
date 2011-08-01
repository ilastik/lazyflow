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
                         QRect, QPoint, QSizeF
from PyQt4.QtGui  import QWidget, QPen, QGraphicsScene, QColor, QGraphicsLineItem, \
                         QImage, QPainter, QGraphicsLineItem

import numpy
import threading
import time

class BrushingModel(QObject):
    brushSizeChanged     = pyqtSignal(int)
    brushColorChanged    = pyqtSignal(QColor)
    brushStrokeAvailable = pyqtSignal(QPointF, QImage)
    
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
        
        #on which layer do we want to draw when self.drawingEnabled?
        self.drawOnto = None
        
        #an empty scene, where we add all drawn line segments
        #a QGraphicsLineItem, and which we can use to then
        #render to an image
        self.scene = QGraphicsScene()

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
        print "BrushingModel.beginDrawing(pos=%r, shape=%r)" % (pos, shape)
        self.shape = shape
        self.scene.clear()
        self.bb = QRect()
        if self.erasing:
            self.penVis.setColor(self.erasingColor)
        else:
            self.penVis.setColor(self.drawColor)
        self.pos = QPointF(pos.x()+0.0001, pos.y()+0.0001)
        line = self.moveTo(pos)
        return line

    def endDrawing(self, pos):
        print "BrushingModel.endDrawing(pos=%r)" % (pos)
        
        self.moveTo(pos)

        tempi = QImage(QSize(self.bb.width(), self.bb.height()), QImage.Format_ARGB32_Premultiplied) #TODO: format
        tempi.fill(0)
        painter = QPainter(tempi)
        self.scene.render(painter, target=QRectF(), source=QRectF(QPointF(self.bb.x(), self.bb.y()), QSizeF(self.bb.width(), self.bb.height())))
        painter.end()
        
        self.brushStrokeAvailable.emit(QPointF(self.bb.x(), self.bb.y()), tempi)

    def dumpDraw(self, pos):
        res = self.endDrawing(pos)
        self.beginDrawing(pos, self.shape)
        return res

    def moveTo(self, pos):
        oldX, oldY = self.pos.x(), self.pos.y()
        x,y = pos.x(), pos.y()
        
        #print "BrushingModel.moveTo(pos=%r)" % (pos) 
        line = QGraphicsLineItem(oldX, oldY, x, y)
        line.setPen(self.penDraw)
        self.scene.addItem(line)
        
        #update bounding Box 
        if not self.bb.isValid():
            self.bb = QRect(QPoint(x,y), QSize(1,1))
        #grow bounding box
        self.bb.setLeft(  min(self.bb.left(),   max(0,             x-self.brushSize/2-1) ) )
        self.bb.setRight( max(self.bb.right(),  min(self.shape[0], x+self.brushSize/2+1) ) )
        self.bb.setTop(   min(self.bb.top(),    max(0,             y-self.brushSize/2-1) ) )
        self.bb.setBottom(max(self.bb.bottom(), min(self.shape[1], y+self.brushSize/2+1) ) )
        
        #update/move position
        self.pos = pos

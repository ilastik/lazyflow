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

from PyQt4.QtCore import Qt, QRectF, QPointF
from PyQt4.QtGui import QGraphicsItem, QPen

#*******************************************************************************
# S l i c e I n t e r s e c t i o n M a r k e r                                *
#*******************************************************************************

class SliceIntersectionMarker(QGraphicsItem) :
    """
    Marks a line within a ImageView2D/ImageScene2D
    """
    
    def boundingRect(self):
        return QRectF(0,0, self._width, self._height);
    
    def __init__(self):
        QGraphicsItem.__init__(self)
        
        self._width = 0
        self._height = 0
              
        self.penX = QPen(Qt.red, 2)
        self.penX.setCosmetic(True)
        
        self.penY = QPen(Qt.green, 2)
        self.penY.setCosmetic(True)
        
        self.x = 0
        self.y = 0
        
        self.isVisible = True

    #be careful: QGraphicsItem has a shape() method, which
    #we cannot override, therefore we choose this name
    @property
    def sceneShape(self):
        return (self._width, self._height)
    @sceneShape.setter
    def sceneShape(self, shape2D):
        self._width = shape2D[0]
        self._height = shape2D[1]

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
            painter.drawLine(QPointF(0.0,self.y), QPointF(self._width, self.y))
            
            painter.setPen(self.penX)
            painter.drawLine(QPointF(self.x, 0), QPointF(self.x, self._height))

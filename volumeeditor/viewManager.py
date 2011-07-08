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
import time, copy
from functools import partial

def posView2D(self, pos3d, axis):
    """convert from a 3D position to a 2D position on the slicing plane
       perpendicular to axis"""
    del pos3d[axis]
    return pos3d

#*******************************************************************************
# V i e w M a n a g e r                                                        *
#*******************************************************************************

class ViewManager(QObject):
    sliceChanged = pyqtSignal(int,int)
    
    def __init__(self, imageView2Ds, image, time = 0, position = [0, 0, 0], channel = 0):
        QObject.__init__(self)
        assert len(imageView2Ds) == 3
        self._views = imageView2Ds
        self._image = image
        self._time = time
        self._position = position
        self._channel = channel
        self._beginStackIndex = 0
        self._endStackIndex   = 1
    
        self._cursorPos  = None
        self._slicingPos = None
        self._activeView = None
        
        axisLabels = ["X:", "Y:", "Z:"]
        for i in range(3):
            v = self._views[i]
            v.mouseMoved.connect(partial(self._onCursorCoordinates, i))
            v.shape = self.imageShape(axis=i)
            v.slices = self.imageExtent(axis=i)
            v.name = axisLabels[i]
    
    def _onCursorCoordinates(self, axis, x, y):
        coor = copy.copy(self._cursorPos)
        if axis == 0:
            self.coor[1] = x
            self.coor[2] = y
        if axis == 1:
            self.coor[0] = x
            self.coor[2] = y
        if axis == 2:
            self.coor[0] = x
            self.coor[1] = y
        #set the new coordinate
        self.cursorPos = coor
    
    @property
    def cursorPos(self):
        return self._cursorPos
    @cursorPos.setter
    def cursorPos(self, coordinates):
        self._cursorPos = coordinates
        self._updateCrossHairCursor()
    
    @property
    def slicingPos(self):
        return self._slicingPos
    @cursorPos.setter
    def slicingPos(self, coordinates):
        self._slicingPos = coordinates
    
    def _updateCrossHairCursor(self):
        x,y = posView2D(self.cursorPos, axis=self.activeView)
        self._views[self.activeView].crossHairCursor.showXYPosition(x,y)
        
        if self.activeView == 0: # x-axis
            if len(self._imageViews) > 2:
                yView = self._views[1].crossHairCursor
                zView = self._views[2].crossHairCursor
                
                yView.setVisible(False)
                zView.showYPosition(x, y)
        elif self.activeView == 1: # y-axis
            xView = self._views[0].crossHairCursor
            zView = self._views[2].crossHairCursor
            
            zView.showXPosition(x, y)
            xView.setVisible(False)
        else: # z-axis
            xView = self._views[0].crossHairCursor
            yView = self._views[1].crossHairCursor
                
            xView.showXPosition(y, x)
            yView.showXPosition(x, y)
        
    @property
    def activeView(self):
        return self._activeView
    @activeView.setter
    def activeView(self, view):
        self._activeView = view
    
    def imageShape(self, axis):
        """returns the 2D shape of slices perpendicular to axis"""
        shape = self._image.shape
        if len(shape) == 2:
            return shape
        else:
            shape = list(shape)
            del shape[axis]
            return numpy.asarray(shape)
    
    def imageExtent(self, axis):
        """returns the 1D extent of the image along axis"""
        return self._image.shape[axis]
        
    def setTime(self, time):
        if self._time != time:
            self._time = time
            self.__updated()
    
    @property    
    def time(self):
        return self._time
    
    @property
    def shape(self):
        return self._image.shape
        
    def setSlice(self, num, axis):
        if num < 0 or num >= self._image.shape[axis]:
            #print "could not setSlice: shape=%r, but axis=%d and num=%d" % (self._image.shape, axis, num)
            return
        
        if self._position[axis] != num:
            self._position[axis] = num
            self.sliceChanged.emit(num, axis)
    
    def changeSliceDelta(self, axis, delta):
        self.setSlice(self.position[axis] + delta, axis)
    
    @property        
    def slicePosition(self):
        return self._position

    @property
    def position(self):
        return self._position
    
    def setChannel(self, channel):
        self._channel = channel

    @property
    def channel(self):
        return self._channel
    
    def getVisibleState(self):
        return [self._time, self._position[0], self._position[1], self._position[2], self._channel]
    
    def __updated(self):
        #self.emit(SIGNAL('viewChanged(ViewManager)'), self) #FIXME
        pass

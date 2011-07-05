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

from ilastikdeps.core.volume import DataAccessor

import numpy
import threading
import time

#*******************************************************************************
# V i e w M a n a g e r                                                        *
#*******************************************************************************

class ViewManager(QObject):
    sliceChanged = pyqtSignal(int,int)
    
    def __init__(self, image, time = 0, position = [0, 0, 0], channel = 0):
        QObject.__init__(self)
        self._image = image
        self._time = time
        self._position = position
        self._channel = channel
        self._beginStackIndex = 0
        self._endStackIndex   = 1
    
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

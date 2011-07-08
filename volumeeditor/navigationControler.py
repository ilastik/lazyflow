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

def posView2D(pos3d, axis):
    pos2d = copy.deepcopy(pos3d)
    """convert from a 3D position to a 2D position on the slicing plane
       perpendicular to axis"""
    del pos2d[axis]
    return pos2d

#*******************************************************************************
# NavigationControler                                                          *
#*******************************************************************************

class NavigationControler(QObject):
    '''Controler for navigating through the volume.

    Handles the following signals:
    cursorPosition -- position of the crosshair cursor
    relativeSliceChange -- switch to a slice relative to the current
    absoluteSliceChange -- switch to a slice based on an absolute value

    '''
    ##
    ## properties
    ##
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
    @slicingPos.setter
    def slicingPos(self, pos):
        print "setting slicing position to", pos
        self._slicingPos = pos
        self._updateSliceIntersection()

    @property
    def activeView(self):
        return self._activeView
    @activeView.setter
    def activeView(self, view):
        self._activeView = view

    @property
    def shape( self ):
        return self._volume.shape

    @property    
    def time( self ):
        return self._time
    @time.setter
    def time( self, value ):
        self._time = value

    @property
    def channel( self ):
        return self._channel
    @channel.setter
    def channel( self, value):
        self._channel = value
    
    @property
    def axisColors( self ):
        return self._axisColors
    @axisColors.setter
    def axisColors( self, colors ):
        self._axisColors = colors



    def __init__(self, imageView2Ds, volume, time = 0, channel = 0):
        QObject.__init__(self)
        assert len(imageView2Ds) == 3
        self._views = imageView2Ds
        self._volume = volume
        self._beginStackIndex = 0
        self._endStackIndex   = 1
    
        self._cursorPos  = [0,0,0]
        self._slicingPos = [0,0,0]
        self._activeView = 0
        self._time = time
        self._channel = channel
        self._axisColors = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]
        
        axisLabels = ["X:", "Y:", "Z:"]
        for i in range(3):
            v = self._views[i]
            v.mouseMoved.connect(partial(self.onCursorPosition, axis=i))
            v.changeSliceDelta.connect(partial(self.onRelativeSliceChange, axis=i))
            v.shape = self.sliceShape(axis=i)
            v.slices = self.volumeExtent(axis=i)
            v.name = axisLabels[i]
            
            x,y = posView2D([0,1,2], axis=i)
            v._sliceIntersectionMarker.setColor(self.axisColors[x], self.axisColors[y])


    
    ##
    ## incoming signal handling
    ##
    def onCursorPosition(self, x, y, axis):
        '''Change position of the crosshair cursor.

        x,y  -- cursor position on a certain image scene
        axis -- perpendicular axis [0,1,2]
 
        '''
        #we get the 2D coordinates x,y from the view that
        #shows the projection perpendicular to axis
        #set this view as active
        self.activeView = axis
        print "ACTIVE VIEW:", axis, x, y
        
        coor = copy.copy(self._cursorPos)
        if axis == 0:
            coor[1] = x
            coor[2] = y
        if axis == 1:
            coor[0] = x
            coor[2] = y
        if axis == 2:
            coor[0] = x
            coor[1] = y
        #set the new coordinate
        self.cursorPos = coor

    def onRelativeSliceChange(self, delta, axis):
        '''Change slice along a certain axis relative to current slice.

        delta  -- add delta to current slice position [positive or negative int]
        axis -- along which axis [0,1,2]
 
        '''
        print "CHANGE SLICE DELTA"
        newSlice = self.slicingPos[axis] + delta
        if newSlice < 0 or newSlice > self.volumeExtent(axis):
            return
        newPos = copy.copy(self.slicingPos)
        newPos[axis] = newSlice
        self.slicingPos = newPos

    def onAbsoluteSliceChange(self, value, axis):
        '''Change slice along a certain axis.

        value  -- slice number
        axis -- along which axis [0,1,2]
 
        '''
        raise NotImplementedError


                
    def sliceShape(self, axis):
        """returns the 2D shape of slices perpendicular to axis"""
        shape = self._volume.shape
        if len(shape) == 2:
            return shape
        else:
            shape = list(shape)
            del shape[axis]
            return numpy.asarray(shape)
    
    def volumeExtent(self, axis):
        """returns the 1D extent of the volume along axis"""
        return self._volume.shape[axis]


    
    def _updateCrossHairCursor(self):
        x,y = posView2D(self.cursorPos, axis=self.activeView)
        self._views[self.activeView]._crossHairCursor.showXYPosition(x,y)
        
        if self.activeView == 0: # x-axis
            yView = self._views[1]._crossHairCursor
            zView = self._views[2]._crossHairCursor
            
            yView.setVisible(False)
            zView.showYPosition(x, y)
        elif self.activeView == 1: # y-axis
            xView = self._views[0]._crossHairCursor
            zView = self._views[2]._crossHairCursor
            
            zView.showXPosition(x, y)
            xView.setVisible(False)
        else: # z-axis
            xView = self._views[0]._crossHairCursor
            yView = self._views[1]._crossHairCursor
                
            xView.showXPosition(y, x)
            yView.showXPosition(x, y)
    
    def _updateSliceIntersection(self):
        for axis, v in enumerate(self._views):
            x,y = posView2D(self.slicingPos, axis)
            print "move marker to position", x ,y
            v._sliceIntersectionMarker.setPosition(x,y)
#    def setSlice(self, num, axis):
#        if num < 0 or num >= self._volume.shape[axis]:
#            #print "could not setSlice: shape=%r, but axis=%d and num=%d" % (self._volume.shape, axis, num)
#            return
#        
#        if self._position[axis] != num:
#            self._position[axis] = num
#            self.sliceChanged.emit(num, axis)
#    
#    def _changeSliceDelta(self, delta, axis):
#        self.setSlice(self.position[axis] + delta, axis)


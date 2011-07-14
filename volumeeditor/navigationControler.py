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

from PyQt4.QtCore import QObject
from PyQt4.QtGui  import QColor

import numpy
import time, copy
from functools import partial

def posView2D(pos3d, axis):
    pos2d = copy.deepcopy(pos3d)
    """convert from a 3D position to a 2D position on the slicing plane
       perpendicular to axis"""
    del pos2d[axis]
    return pos2d

#*******************************************************************************
# N a v i g a t i o n C o n t r o l e r                                        *
#*******************************************************************************

class NavigationControler(QObject):
    '''Controler for navigating through the volume.'''
    ##
    ## properties
    ##

    @property
    def activeView(self):
        return self._activeView
    @activeView.setter
    def activeView(self, view):
        self._activeView = view
    
    @property
    def axisColors( self ):
        return self._axisColors
    @axisColors.setter
    def axisColors( self, colors ):
        self._axisColors = colors
        self._views[0]._sliceIntersectionMarker.setColor(self.axisColors[1], self.axisColors[2])
        self._views[1]._sliceIntersectionMarker.setColor(self.axisColors[0], self.axisColors[2])
        self._views[2]._sliceIntersectionMarker.setColor(self.axisColors[0], self.axisColors[1])
        for axis, v in enumerate(self._views):
            v.hud.bgColor = self.axisColors[axis]
        
    @property
    def indicateSliceIntersection(self):
        return self._indicateSliceIntersection
    @indicateSliceIntersection.setter
    def indicateSliceIntersection(self, show):
        self._indicateSliceIntersection = show
        for v in self._views:
            v._sliceIntersectionMarker.setVisibility(show)
        
    def __init__(self, imageView2Ds, positionModel, overlaywidget, time = 0, channel = 0):
        '''
        volumeShape - 3D shape of the voxel data

        '''
        QObject.__init__(self)
        assert len(imageView2Ds) == 3

        # init fields
        self._views = imageView2Ds
        self._model = positionModel
        self._overlaywidget = overlaywidget
        self._beginStackIndex = 0
        self._endStackIndex   = 1

        # init views
        axisLabels = ["X:", "Y:", "Z:"]
        for i in range(3):
            v = self._views[i]
            v.mouseMoved.connect(partial(self.onCursorPosition, axis=i))
            v.mouseDoubleClicked.connect(partial(self.onSlicePosition, axis=i))
            v.changeSliceDelta.connect(partial(self.onRelativeSliceChange, axis=i))
            v.shape = self._model.sliceShape(axis=i)
            v.slices = self._model.volumeExtent(axis=i)
            
            v.hud.label = axisLabels[i]
            v.hud.minimum = 0
            v.hud.maximum = self._model.volumeExtent(i)
            v.hud.sliceSelector.valueChanged.connect(partial(self.onAbsoluteSliceChange, axis=i))
        self._views[0].swapAxes()

        # init property fields
        self._activeView = 0
        self._axisColors = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]

        # call property setters to trigger updates etc. 
        self.activeView = 0
        self.axisColors = [QColor(255,0,0,255), QColor(0,255,0,255), QColor(0,0,255,255)]


    
    ##
    ## incoming signal handling
    ##
    def onIndicateSliceIntersectionToggle(self, show):
        self.indicateSliceIntersection = show
    
    def onChannelChange(self, channel, axis):
        print "channel change not implemented"
        #if len(self.overlayWidget.overlays) > 0:
        #    ov = self.overlayWidget.getOverlayRef("Raw Data")
        #     if ov.shape[-1] == self._shape[-1]:
        #         self.overlayWidget.getOverlayRef("Raw Data").channel = channel

    
    def onCursorPosition(self, x, y, axis):
        '''Change position of the crosshair cursor.

        x,y  -- cursor position on a certain image scene
        axis -- perpendicular axis [0,1,2]
 
        '''
        #we get the 2D coordinates x,y from the view that
        #shows the projection perpendicular to axis
        #set this view as active
        self.activeView = axis
        
        newPos = copy.copy(self._model.cursorPos)
        if axis == 0:
            newPos[1] = x
            newPos[2] = y
        if axis == 1:
            newPos[0] = x
            newPos[2] = y
        if axis == 2:
            newPos[0] = x
            newPos[1] = y

        if newPos == self._model.cursorPos:
            return
        if not self._positionValid(newPos):
            return

        self._model.cursorPos = newPos
        #update the cross hair cursor after the model has changed
        self._updateCrossHairCursor()

    def _positionValid(self, pos):
        for i in range(3):
            if pos[i] < 0 or pos[i] >= self._model.shape[i]:
                return False
        return True

    def onSlicePosition(self, x, y, axis):
        newPos = copy.copy(self._model.slicingPos)
        i,j = posView2D([0,1,2], axis)
        newPos[i] = x
        newPos[j] = y
        if newPos == self._model.slicingPos:
            return
        if not self._positionValid(newPos):
            return
        
        for i in 0,1,2:
            self._updateSlice(newPos[i], i)
        
        self._model.slicingPos = newPos
        #update the slice intersection after the model has changed
        self._updateSliceIntersection()

    def onRelativeSliceChange(self, delta, axis):
        '''Change slice along a certain axis relative to current slice.

        delta  -- add delta to current slice position [positive or negative int]
        axis -- along which axis [0,1,2]
 
        '''
        if delta == 0:
            return
        newSlice = self._model.slicingPos[axis] + delta
        if newSlice < 0 or newSlice > self._model.volumeExtent(axis):
            return
        newPos = copy.copy(self._model.slicingPos)
        newPos[axis] = newSlice
        
        self._updateSlice(newSlice, axis)
        self._model.slicingPos = newPos

    def onAbsoluteSliceChange(self, value, axis):
        '''Change slice along a certain axis.

        value  -- slice number
        axis -- along which axis [0,1,2]
 
        '''
        if value < 0 or value > self._model.volumeExtent(axis):
            return
        newPos = copy.copy(self._model.slicingPos)
        newPos[axis] = value
        if not self._positionValid(newPos):
            return
        self._model.slicingPos = newPos
    
    def _updateCrossHairCursor(self):
        x,y = posView2D(self._model.cursorPos, axis=self.activeView)
        self._views[self.activeView]._crossHairCursor.showXYPosition(x,y)
        
        if self.activeView == 0: # x-axis
            yView = self._views[1]._crossHairCursor
            zView = self._views[2]._crossHairCursor
            
            #in case of the x-view, yViewYpos and zViewYpos has to be updated
            #adding 0.5 to make line snap into middle of pixels, like the croshair
            yView.showYPosition(y + 0.5, x)
            zView.showYPosition(x + 0.5, y)
        elif self.activeView == 1: # y-axis
            xView = self._views[0]._crossHairCursor
            zView = self._views[2]._crossHairCursor
            
            #in case of the y-view, yViewYpos and zViewXpos has to be updated
            #adding 0.5 to make line snap into middle of pixels, like the croshair
            xView.showYPosition(y + 0.5, x)
            zView.showXPosition(x, y)
        else: # z-axis
            xView = self._views[0]._crossHairCursor
            yView = self._views[1]._crossHairCursor
                
            #in case of the z-view, xViewYpos and yViewXpos has to be updated
            #no adding required in this case   
            xView.showXPosition(y, x)
            yView.showXPosition(x, y)
    
    def _updateSliceIntersection(self):
        for axis, v in enumerate(self._views):
            x,y = posView2D(self._model.slicingPos, axis)
            v._sliceIntersectionMarker.setPosition(x,y)

    def _updateSlice(self, num, axis):
        if num < 0 or num >= self._model.volumeExtent(axis):
            raise Exception("NavigationControler._setSlice(): invalid slice number")

        # update view
        self._views[axis].hud.sliceSelector.setValue(num)

        # update model
        overlays = []
        for item in reversed(self._overlaywidget.overlays):
            if item.visible:
                overlays.append(item.getOverlaySlice(num, axis, 0, item.channel))
        if len(self._overlaywidget.overlays) == 0 \
           or self._overlaywidget.getOverlayRef("Raw Data") is None:
            return
        
        rawData = self._overlaywidget.getOverlayRef("Raw Data")._data
        image = rawData.getSlice(num,\
                                 axis, 0,\
                                 self._overlaywidget.getOverlayRef("Raw Data").channel)

        #make sure all tiles are regenerated
        self._views[axis].scene().markTilesDirty()
        self._views[axis].scene().setContent(self._views[axis].viewportRect(), image, overlays) 



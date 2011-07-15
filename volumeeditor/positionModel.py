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

import copy, numpy

from PyQt4.QtCore import QObject, pyqtSignal

#*******************************************************************************
# P o s i t i o n M o d e l                                                    *
#*******************************************************************************

class PositionModel(QObject):
    cursorPositionChanged  = pyqtSignal(object, object)
    slicingPositionChanged = pyqtSignal(object, object)
    viewActive             = pyqtSignal(int)
    
    def __init__(self, volumeShape, parent=None):
        QObject.__init__(self, parent)
        
        #init property fields
        self._cursorPos  = [0,0,0]
        self._slicingPos = [0,0,0]
        self._time       = 0
        self._channel    = 0
        self._volumeShape= volumeShape
        #call property setters to trigger updates etc. 
        self.cursorPos   = self._cursorPos
        self.slicingPos  = self._slicingPos
        self.time        = self._time
        self.channel     = self._channel
        
    def sliceShape(self, axis):
        """returns the 2D shape of slices perpendicular to axis"""
        shape = self._volumeShape
        if len(shape) == 2:
            return shape
        else:
            shape = list(shape)
            del shape[axis]
            return numpy.asarray(shape)
    
    def volumeExtent(self, axis):
        """returns the 1D extent of the volume along axis"""
        return self._volumeShape[axis]
    
    @property
    def activeView(self):
        return self._activeView
    @activeView.setter
    def activeView(self, view):
        self._activeView = view
        self.viewActive.emit(view)
        
    @property
    def shape( self ):
        return self._volumeShape
        
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
    def cursorPos(self):
        return self._cursorPos
    @cursorPos.setter
    def cursorPos(self, coordinates):
        if coordinates == self._cursorPos:
            return
        oldPos = copy.copy(self._cursorPos)
        self._cursorPos = coordinates
        print "PositionModel emitting 'cursorPositionChanged(%r, %r)'" % (oldPos, self.slicingPos)
        self.cursorPositionChanged.emit(oldPos, self.cursorPos)
    
    @property
    def slicingPos(self):
        return self._slicingPos
    @slicingPos.setter
    def slicingPos(self, pos):
        if pos == self._slicingPos:
            return
        oldPos = copy.copy(self._slicingPos)
        self._slicingPos = pos
        print "PositionModel emitting 'slicingPositionChanged(%r, %r)'" % (oldPos, self.slicingPos)
        self.slicingPositionChanged.emit(oldPos, self.slicingPos)
        
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

from PyQt4.QtCore import pyqtSignal, QObject, QThread, Qt, QSize, QPointF, QRectF, \
                         QRect, QPoint
from PyQt4.QtGui  import QWidget, QPen, QGraphicsScene, QColor, QGraphicsLineItem, \
                         QImage, QPainter, QGraphicsLineItem

from ilastikdeps.core.volume import DataAccessor

import numpy
import threading
import time

from collections import deque

#*******************************************************************************
# I m a g e S a v e T h r e a d                                                *
#*******************************************************************************

class ImageSaveThread(QThread):
    def __init__(self, parent):
        QThread.__init__(self, None)
        self.ve = parent
        self.queue = deque()
        self.imageSaved = threading.Event()
        self.imageSaved.clear()
        self.imagePending = threading.Event()
        self.imagePending.clear()
        self.stopped = False
        self.previousSlice = None
        
    def run(self):
        while not self.stopped:
            self.imagePending.wait()
            while len(self.queue)>0:
                stuff = self.queue.pop()
                if stuff is not None:
                    filename, timeOffset, sliceOffset, format = stuff
                    if self.ve.image.shape[1]>1:
                        axis = 2
                        self.previousSlice = self.ve.sliceSelectors[axis].value()
                        for t in range(self.ve.image.shape[0]):
                            for z in range(self.ve.image.shape[3]):                   
                                self.filename = filename
                                if (self.ve.image.shape[0]>1):
                                    self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                                self.filename = self.filename + ("_z%05i" %(z+sliceOffset))
                                self.filename = self.filename + "." + format
                        
                                #only change the z slice display
                                self.ve.imageScenes[axis].thread.queue.clear()
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
                                self.ve.updateTimeSliceForSaving(t, z, axis)
                                
                                
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
        
                                self.ve.imageScenes[axis].saveSlice(self.filename)
                    else:
                        axis = 0
                        for t in range(self.ve.image.shape[0]):                 
                            self.filename = filename
                            if (self.ve.image.shape[0]>1):
                                self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                            self.filename = self.filename + "." + format
                            self.ve.imageScenes[axis].thread.queue.clear()
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.updateTimeSliceForSaving(t, self.ve.viewManager.slicePosition[0], axis)                              
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.imageScenes[axis].saveSlice(self.filename)
            self.imageSaved.set()
            self.imagePending.clear()
            if self.previousSlice is not None:
                self.ve.sliceSelectors[axis].setValue(self.previousSlice)
                self.previousSlice = None

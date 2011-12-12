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

from PyQt4.QtCore import QPointF, QRectF

import numpy

#*******************************************************************************
# P a t c h A c c e s s o r                                                    *
#*******************************************************************************

class PatchAccessor():
    """
    Cut a given 2D shape into patches of given rectangular size
    """
    
    def __init__(self, size_x, size_y, blockSize = 128):
        """
        (size_x, size_y) -- 2D shape
        blockSize        -- maximum width/height of patches
        
        Constructs a PatchAccessor that will divide the given shape
        into patches that have a maximum given size.
        """
        
        self._blockSize = blockSize
        self.size_x = size_x
        self.size_y = size_y

        self._cX = int(numpy.ceil(1.0 * size_x / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = size_x % self._blockSize
        if self._cXend < self._blockSize / 3 and self._cXend != 0 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0

        self._cY = int(numpy.ceil(1.0 * size_y / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = size_y % self._blockSize
        if self._cYend < self._blockSize / 3 and self._cYend != 0 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0


        self.patchCount = self._cX * self._cY

    def __len__(self):
        return self.patchCount

    def getPatchBounds(self, blockNum, overlap = 0):
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX

        startx = max(0, x*self._blockSize - overlap)
        endx = min(self.size_x, (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self.size_x

        starty = max(0, y*self._blockSize - overlap)
        endy = min(self.size_y, (y+1)*self._blockSize + overlap)
        if y+1 >= self._cY:
            endy = self.size_y

        return [startx,endx,starty,endy]

    def patchRectF(self, blockNum, overlap = 0):
        startx,endx,starty,endy = self.getPatchBounds(blockNum, overlap)
        return QRectF(QPointF(startx, starty), QPointF(endx,endy))

    def getPatchesForRect(self,startx,starty,endx,endy):
        sx = int(numpy.floor(1.0 * startx / self._blockSize))
        ex = int(numpy.ceil(1.0 * endx / self._blockSize))
        sy = int(numpy.floor(1.0 * starty / self._blockSize))
        ey = int(numpy.ceil(1.0 * endy / self._blockSize))
        
        if ey > self._cY:
            ey = self._cY

        if ex > self._cX :
            ex = self._cX

        nums = []
        for y in range(sy,ey):
            nums += range(y*self._cX+sx,y*self._cX+ex)
        
        return nums

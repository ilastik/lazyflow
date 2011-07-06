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

from PyQt4.QtGui import QGraphicsScene, QImage
from OpenGL.GL import *
from OpenGL.GLU import *

from patchAccessor import PatchAccessor
from imageSceneRenderer import ImageSceneRenderer

class ImageScene2D(QGraphicsScene):
    blockSize = 128
    
    @property
    def useGL(self):
        return self._glWidget is not None
    
    def __init__(self, shape2D, glWidget):
        QGraphicsScene.__init__(self)
        self._glWidget = glWidget
        self._useGL = (glWidget != None)
        self._shape2D = shape2D
        
        self.imagePatches   = []
        self._patchAccessor = PatchAccessor(*self._shape2D, blockSize=self.blockSize)

        if False: #self._useGL:    
            self._glWidget.context().makeCurrent()
            self.scene().tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D,self.scene().tex)
            #print "generating OpenGL texture of size %d x %d" % (self.scene.image.width(), self.scene.image.height())
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, \
                         self.shape2D[0], self.shape2D[1], \
                         0, GL_RGB, GL_UNSIGNED_BYTE, \
                         ctypes.c_void_p(self.scene().image.bits().__int__()))
        else:
            for i in range(self._patchAccessor.patchCount):
                b = self._patchAccessor.getPatchBounds(i, 0)
                self.imagePatches.append( QImage(b[1]-b[0], b[3] -b[2], QImage.Format_RGB888) )
    
            self.setSceneRect(0,0, *self._shape2D)
    
        self._ImageSceneRenderer = ImageSceneRenderer(self._patchAccessor, self.imagePatches, self._glWidget)

    def drawBackgroundSoftware(self, painter, rect):
        drawnTiles = 0
        for i,img in enumerate(self.imagePatches):
            print self._patchAccessor.getPatchBounds(i)
            r = self._patchAccessor.patchRectF(i)
            print r
            if not r.intersect(rect): continue
            painter.drawImage(r.topLeft(), img)
            drawnTiles +=1
        print "ImageView2D.drawBackgroundSoftware: drew %d of %d tiles" % (drawnTiles, len(self.imagePatches))

    def drawBackgroundGL(self, painter, rect):
        return 
        self._glWidget.context().makeCurrent()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.tex <= -1:
            return

        #self.glWidget.drawTexture(QRectF(self.image.rect()),self.tex)
        d = painter.device()
        dc = sip.cast(d,QGLFramebufferObject)

        rect = QRectF(self.image.rect())
        tl = rect.topLeft()
        br = rect.bottomRight()
        
        #flip coordinates since the texture is flipped
        #this is due to qimage having another representation thatn OpenGL
        rect.setCoords(tl.x(),br.y(),br.x(),tl.y())
        
        #switch corrdinates if qt version is small
        painter.beginNativePainting()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        dc.drawTexture(rect,self.tex)
        painter.endNativePainting()

    def drawBackground(self, painter, rect):
        if self.useGL:
            self.drawBackgroundGL(painter, rect)
        else:
            self.drawBackgroundSoftware(painter, rect)
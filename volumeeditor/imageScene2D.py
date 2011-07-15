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

from PyQt4.QtCore import QRect, QRectF, QTimer, pyqtSignal
from PyQt4.QtGui import QGraphicsScene, QImage
from PyQt4.QtOpenGL import QGLWidget
from OpenGL.GL import GL_CLAMP_TO_EDGE, GL_COLOR_BUFFER_BIT, GL_DEPTH_TEST, \
                      GL_NEAREST, GL_QUADS, GL_TEXTURE_2D, \
                      GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, \
                      GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, \
                      glBegin, glEnd, glBindTexture, glClearColor, glDisable, \
                      glEnable, glRectf, glClear, glTexCoord2f, \
                      glTexParameteri, glVertex2f, glColor4f

from patchAccessor import PatchAccessor
from imageSceneRendering import ImageSceneRenderThread

class ImagePatch(object):    
    def __init__(self, rectF):
        assert(type(rectF) == QRectF)
        
        self.rectF  = rectF
        self.rect   = QRect(round(rectF.x()),     round(rectF.y()), \
                            round(rectF.width()), round(rectF.height()))
        self._image  = QImage(self.rect.width(), self.rect.height(), QImage.Format_ARGB32_Premultiplied)
        self.texture = -1
        self.dirty = True

    @property
    def height(self):
        return self.rect.height()
    
    @property
    def width(self):
        return self.rect.width()

    def drawTexture(self):
        tx = self.rect.x()
        ty = self.rect.y()
        w = self.rect.width()
        h = self.rect.height()
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(tx, ty)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(tx + w, ty)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(tx + w, ty + h)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(tx, ty + h)
        glEnd()

    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, img):
        self._image = img
        self.dirty = False

class ImageScene2D(QGraphicsScene):
    # the data to be displayed was changed
    contentChanged = pyqtSignal()

    # base patch size: blockSize x blockSize
    blockSize = 128
    # overlap between patches 
    # positive number prevents rendering artifacts between patches for certain zoom levels
    # increases the base blockSize 
    overlap = 1 
    
    # update delay when a new patch arrives in ms
    glUpdateDelay = 10
    
    def __init__(self, viewport):
        QGraphicsScene.__init__(self)
        self._glWidget = viewport
        self._useGL = isinstance(viewport, QGLWidget)
        self._shape2D = None
        self._updatableTiles = []

        # tile rendering
        self.imagePatches = None
        self._image = None
        self._overlays = None
        self._renderThread = None

    @property
    def shape(self):
        return [self.sceneRect().width(), self.sceneRect().height()]
    @shape.setter
    def shape(self, shape2D):
        assert len(shape2D) == 2
        self.setSceneRect(0,0, *shape2D)
        
        del self._renderThread
        del self.imagePatches
        
        self.imagePatches = []
        patchAccessor = PatchAccessor(*shape2D, blockSize=self.blockSize)
        for i in range(patchAccessor.patchCount):
            r = patchAccessor.patchRectF(i, self.overlap)
            patch = ImagePatch(r)
            self.imagePatches.append(patch)
        self._renderThread = ImageSceneRenderThread(self.imagePatches)
        self._renderThread.start()
        self._renderThread.patchAvailable.connect(self.updatePatch)

    def setContent(self, rect, image, overlays = ()):
        #FIXME: assert we have the right shape
        
        '''ImageScene immediately starts to render tiles, that display the new content.'''
        # store data for later rerendering when the rect changes, but not the data
        self._image = image
        self._overlays = overlays

        #Abandon previous workloads
        self._renderThread.queue.clear()
        self._renderThread.newerDataPending.set()

        #Find all patches that intersect the given 'rect'.
        patches = []
        for i,patch in enumerate(self.imagePatches):
            if patch.dirty and rect.intersects(patch.rectF):
                patches.append(i)
        if len(patches) == 0: return

        #Update these patches using the thread below
        workPackage = [patches, overlays, 0, 255]
        self._renderThread.queue.append(workPackage)
        self._renderThread.dataPending.set()

        self.contentChanged.emit()

    def changeVisibleContent( self, rect ):
        '''Don't change the data to be rendered, but just the visible area.'''
        self.setContent(rect, self._image, self._overlays)

    def updatePatch(self, patchNr):
        p = self.imagePatches[patchNr]
        self._updatableTiles.append(patchNr)
        
        #print "update patch %d" % (patchNr)
        if self._useGL:
            QTimer.singleShot(self.glUpdateDelay, self.update)
        else:
            self.invalidate(p.rectF, QGraphicsScene.BackgroundLayer)

    def drawBackgroundSoftware(self, painter, rect):
        drawnTiles = 0
        for patch in self.imagePatches:
            if not patch.rectF.intersect(rect): continue
            painter.drawImage(patch.rectF.topLeft(), patch.image)
            drawnTiles +=1
        #print "ImageView2D.drawBackgroundSoftware: drew %d of %d tiles" % (drawnTiles, len(self.imagePatches))

    def markTilesDirty(self):
        for patch in self.imagePatches:
            patch.dirty = True
    
    def initializeGL(self):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glClearColor(0.0, 0.0, 0.0, 0.0);
        glClear(GL_COLOR_BUFFER_BIT)

    def drawBackgroundGL(self, painter, rect):
        painter.beginNativePainting()
        
        #This will clear the screen, but also introduce flickering
        glClearColor(0.0, 1.0, 0.0, 1.0);
        glClear(GL_COLOR_BUFFER_BIT);
        
        #update the textures of those patches that were updated
        for t in self._updatableTiles:
            patch = self.imagePatches[t]
            if patch.texture > -1:
                self._glWidget.deleteTexture(patch.texture)
            patch.texture = self._glWidget.bindTexture(patch.image)
            #see 'backingstore' example by Ariya Hidayat
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            #this ensures a seamless transition between tiles
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        self._updatableTiles = []
        
        drawnTiles = 0
        for patch in self.imagePatches:
            if not patch.rectF.intersect(rect): continue
            patch.drawTexture()
            drawnTiles +=1
        
        #  ************************************************
        #  * rectangle s                                  *
        #  *                                              *
        #  *             ***************************      *                   
        #  *             * rectangle r             *      *
        #  *             ***************************      *                   
        #  *                                              *                 
        #  ************************************************
        #r = QRectF(0,0,*self._shape2D)
        #s = rect
        #glColor4f(1.0,0.0,0.0, 1.0)
        #glRectf(s.x(), s.y(), r.x(), s.y()+s.height())
        #glColor4f(0.0,1.0,0.0, 1.0)
        #glRectf(r.x(), s.y(), r.x()+r.width(), s.y()+(r.y()-s.y()))
        #glColor4f(0.0,0.0,1.0, 1.0)
        #glRectf(r.x()+r.width(), s.y(), s.x()+s.width(), s.y()+s.height())
        #glColor4f(1.0,1.0,0.0, 1.0)
        #glRectf(r.x(), r.y()+r.height(), r.x()+r.width(), s.y()+s.height())

        #print "ImageView2D.drawBackgroundGL: drew %d of %d tiles" % (drawnTiles, len(self.imagePatches))
        painter.endNativePainting()

    def drawBackground(self, painter, rect):
        if self._useGL:
            self.drawBackgroundGL(painter, rect)
        else:
            self.drawBackgroundSoftware(painter, rect)

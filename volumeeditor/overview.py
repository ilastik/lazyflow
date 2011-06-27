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

from PyQt4.QtGui import QWidget, QSizePolicy
from PyQt4.QtOpenGL import QGLWidget, QGLFramebufferObject

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except Exception, e:
    print e
    pass

#*******************************************************************************
# O v e r v i e w S c e n e F a c t o r y                                      *
#*******************************************************************************
class OverviewSceneFactory:
    @staticmethod
    def getOverviewScene(imageScenes, viewManager, shape, sharedOpenGLWidget = None):
        if sharedOpenGLWidget is not None:
            return OverviewSceneGL(imageScenes, viewManager, shape, sharedOpenGLWidget)
        else:
            return OverviewSceneDummy()

#*******************************************************************************
# O v e r v i e w S c e n e D u m m y                                          *
#*******************************************************************************

class OverviewSceneDummy(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        pass
    
    def display(self, axis):
        pass

    def redisplay(self):
        pass
    
#*******************************************************************************
# O v e r v i e w S c e n e G L                                                *
#*******************************************************************************

class OverviewSceneGL(QGLWidget):
    def __init__(self, images, viewManager, shape, sharedOpenGLWidget):
        QGLWidget.__init__(self, shareWidget = sharedOpenGLWidget)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.viewManger = viewManager
        self.images = images
        self.sceneShape = shape
        
        self.sceneItems = []
        self.initialized = False
        self.tex = []
        self.tex.append(-1)
        self.tex.append(-1)
        self.tex.append(-1)

    def display(self, axis):
        if self.initialized is True:
            #self.initializeGL()
            self.makeCurrent()
            self.paintGL(axis)
            self.swapBuffers()
            
    def redisplay(self):
        if self.initialized is True:
            for i in range(3):
                self.makeCurrent()
                self.paintGL(i)
            self.swapBuffers()        

    def paintGL(self, axis = None):
        '''
        Drawing routine
        '''
        pix0 = self.images[0].pixmap
        pix1 = self.images[1].pixmap
        pix2 = self.images[2].pixmap

        maxi = max(pix0.width(),pix1.width())
        maxi = max(maxi, pix2.width())
        maxi = max(maxi, pix0.height())
        maxi = max(maxi, pix1.height())
        maxi = max(maxi, pix2.height())

        ratio0w = 1.0 * pix0.width() / maxi
        ratio1w = 1.0 * pix1.width() / maxi
        ratio2w = 1.0 * pix2.width() / maxi

        ratio0h = 1.0 * pix0.height() / maxi
        ratio1h = 1.0 * pix1.height() / maxi
        ratio2h = 1.0 * pix2.height() / maxi
       
        glMatrixMode(GL_MODELVIEW)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glRotatef(30,1.0,0.0,0.0)

        glTranslatef(0,-3,-5)        # Move Into The Screen

        glRotatef(-30,0.0,1.0,0.0)        # Rotate The Cube On X, Y & Z

        #glRotatef(180,1.0,0.0,1.0)        # Rotate The Cube On X, Y & Z

        glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode

        glBegin(GL_QUADS)            # Start Drawing The Cube

        glColor3f(1.0,0.0,1.0)            # Set The Color To Violet
        
        glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Top)
        glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Top)
        glVertex3f(-ratio2w, ratio1h, ratio2h)        # Bottom Left Of The Quad (Top)
        glVertex3f( ratio2w, ratio1h, ratio2h)        # Bottom Right Of The Quad (Top)

        glVertex3f( ratio2w,-ratio1h, ratio2h)        # Top Right Of The Quad (Bottom)
        glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Top Left Of The Quad (Bottom)
        glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Bottom)
        glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Bottom)

        glVertex3f( ratio2w, ratio1h, ratio2h)        # Top Right Of The Quad (Front)
        glVertex3f(-ratio2w, ratio1h, ratio2h)        # Top from PyQt4 import QtCore, QtGui, QtOpenGLLeft Of The Quad (Front)
        glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Bottom Left Of The Quad (Front)
        glVertex3f( ratio2w,-ratio1h, ratio2h)        # Bottom Right Of The Quad (Front)

        glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Back)
        glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Back)
        glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Back)
        glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Back)

        glVertex3f(-ratio2w, ratio1h, ratio2h)        # Top Right Of The Quad (Left)
        glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Left)
        glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Left)
        glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Bottom Right Of The Quad (Left)

        glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Right)
        glVertex3f( ratio2w, ratio1h, ratio2h)        # Top Left Of The Quad (Right)
        glVertex3f( ratio2w,-ratio1h, ratio2h)        # Bottom Left Of The Quad (Right)
        glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Right)
        glEnd()                # Done Drawing The Quad


        curCenter = -(( 1.0 * self.viewManger.slicePosition[2] / self.sceneShape[2] ) - 0.5 )*2.0*ratio1h
        if axis is 2:
            self.tex[2] = self.images[2].scene.tex
        if self.tex[2] != -1:
            glBindTexture(GL_TEXTURE_2D,self.tex[2])
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

            glBegin(GL_QUADS) #horizontal quad (e.g. first axis)
            glColor3f(1.0,1.0,1.0)            # Set The Color To White
            glTexCoord2d(0.0, 0.0)
            glVertex3f( -ratio2w,curCenter, -ratio2h)        # Top Right Of The Quad
            glTexCoord2d(1.0, 0.0)
            glVertex3f(+ ratio2w,curCenter, -ratio2h)        # Top Left Of The Quad
            glTexCoord2d(1.0, 1.0)
            glVertex3f(+ ratio2w,curCenter, + ratio2h)        # Bottom Left Of The Quad
            glTexCoord2d(0.0, 1.0)
            glVertex3f( -ratio2w,curCenter, + ratio2h)        # Bottom Right Of The Quad
            glEnd()


            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture

            glBegin(GL_QUADS)
            glColor3f(0.0,0.0,1.0)            # Set The Color To Blue, Z Axis
            glVertex3f( ratio2w,curCenter, ratio2h)        # Top Right Of The Quad (Bottom)
            glVertex3f(- ratio2w,curCenter, ratio2h)        # Top Left Of The Quad (Bottom)
            glVertex3f(- ratio2w,curCenter,- ratio2h)        # Bottom Left Of The Quad (Bottom)
            glVertex3f( ratio2w,curCenter,- ratio2h)        # Bottom Right Of The Quad (Bottom)
            glEnd()

        curCenter = (( (1.0 * self.viewManger.slicePosition[0]) / self.sceneShape[0] ) - 0.5 )*2.0*ratio2w

        if axis is 0:
            self.tex[0] = self.images[0].scene.tex
        if self.tex[0] != -1:
            glBindTexture(GL_TEXTURE_2D,self.tex[0])


            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

            glBegin(GL_QUADS)
            glColor3f(0.8,0.8,0.8)            # Set The Color To White
            glTexCoord2d(1.0, 0.0)
            glVertex3f(curCenter, ratio0h, ratio0w)        # Top Right Of The Quad (Left)
            glTexCoord2d(0.0, 0.0)
            glVertex3f(curCenter, ratio0h, - ratio0w)        # Top Left Of The Quad (Left)
            glTexCoord2d(0.0, 1.0)
            glVertex3f(curCenter,- ratio0h,- ratio0w)        # Bottom Left Of The Quad (Left)
            glTexCoord2d(1.0, 1.0)
            glVertex3f(curCenter,- ratio0h, ratio0w)        # Bottom Right Of The Quad (Left)
            glEnd()

            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture

            glBegin(GL_QUADS)
            glColor3f(1.0,0.0,0.0)            # Set The Color To Red,
            glVertex3f(curCenter, ratio0h, ratio0w)        # Top Right Of The Quad (Left)
            glVertex3f(curCenter, ratio0h, - ratio0w)        # Top Left Of The Quad (Left)
            glVertex3f(curCenter,- ratio0h,- ratio0w)        # Bottom Left Of The Quad (Left)
            glVertex3f(curCenter,- ratio0h, ratio0w)        # Bottom Right Of The Quad (Left)
            glEnd()


        curCenter = (( 1.0 * self.viewManger.slicePosition[1] / self.sceneShape[1] ) - 0.5 )*2.0*ratio2h


        if axis is 1:
            self.tex[1] = self.images[1].scene.tex
        if self.tex[1] != -1:
            glBindTexture(GL_TEXTURE_2D,self.tex[1])

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

            glBegin(GL_QUADS)
            glColor3f(0.6,0.6,0.6)            # Set The Color To White
            glTexCoord2d(1.0, 0.0)
            glVertex3f( ratio1w,  ratio1h, curCenter)        # Top Right Of The Quad (Front)
            glTexCoord2d(0.0, 0.0)
            glVertex3f(- ratio1w, ratio1h, curCenter)        # Top Left Of The Quad (Front)
            glTexCoord2d(0.0, 1.0)
            glVertex3f(- ratio1w,- ratio1h, curCenter)        # Bottom Left Of The Quad (Front)
            glTexCoord2d(1.0, 1.0)
            glVertex3f( ratio1w,- ratio1h, curCenter)        # Bottom Right Of The Quad (Front)
            glEnd()

            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture
            glBegin(GL_QUADS)
            glColor3f(0.0,1.0,0.0)            # Set The Color To Green
            glVertex3f( ratio1w,  ratio1h, curCenter)        # Top Right Of The Quad (Front)
            glVertex3f(- ratio1w, ratio1h, curCenter)        # Top Left Of The Quad (Front)
            glVertex3f(- ratio1w,- ratio1h, curCenter)        # Bottom Left Of The Quad (Front)
            glVertex3f( ratio1w,- ratio1h, curCenter)        # Bottom Right Of The Quad (Front)
            glEnd()

        glFlush()

    def resizeGL(self, w, h):
        '''
        Resize the GL window
        '''

        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 30.0)

    def initializeGL(self):
        '''
        Initialize GL
        '''

        # set viewing projection
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        glDepthFunc(GL_LESS)                # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)                # Enables Depth Testing
        glShadeModel(GL_SMOOTH)                # Enables Smooth Color Shading
        glEnable(GL_TEXTURE_2D)
        glLineWidth( 2.0 );

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 30.0)
        
        self.initialized = True


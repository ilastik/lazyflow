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

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication, QWidget, QSplitter, QColor,\
                        QSizePolicy, QGridLayout
from imageEditorComponents import ImageViewWidget, PositionStatusBar2D
from pixelpipeline.datasources import ArraySource
from imageEditor import ImageEditor
from volumina.layer import GrayscaleLayer
from volumina.layerstack import LayerStackModel
from testing import TwoDtestVolume
import numpy


#*******************************************************************************
# I m a g e E d i t o r W i d g e t                                            *
#*******************************************************************************

class ImageEditorWidget(QWidget):
    def __init__( self, parent=None, editor=None ):
        super(ImageEditorWidget, self).__init__(parent=parent)
        
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setFocusPolicy(Qt.StrongFocus)
        
        if editor!=None:
            self.init(editor)
    
    def init(self, imageEditor):

        self._ie = imageEditor
        
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.updateGeometry()
        self.update()
        
    
    def addImageEditor(self,editor,position=(0,0)):
        
        imageViewWigdet = ImageViewWidget(self, editor.imageView[0])
        positionStatusbar2D = PositionStatusBar2D()
        positionStatusbar2D.create(\
            QColor("green"), QColor("white"), \
            QColor("blue"), QColor("white"),  \
            QColor("gray"), QColor("white") \
        )
        editor.posModel.cursorPositionChanged.connect(positionStatusbar2D.updateCoordLabels)
        imageViewWigdet.addStatusBar(positionStatusbar2D)
        
        self.checkPosition(position)
        self.grid.addWidget(imageViewWigdet,position[0],position[1])
    
    def checkPosition(self,position):
        
        widget = self.grid.itemAtPosition(position[0], position[1])
        if widget:
            self.grid.removeItem(widget)
            freePos = self.getFreePosition()
            self.grid.addItem(widget, freePos[0], freePos[1])
    
    def getFreePosition(self):
        
        i=0
        j=0
        while self.grid.itemAtPosition(i,j):
            while i >= j:
                if self.grid.itemAtPosition(i,j):
                    break
                j=j+1
            i=i+1
            
        return (i,j)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

class testWidget(object):
    
    def __init__(self):
        
        app = QApplication(sys.argv)
    
        s = QSplitter()
   
        editor = self.generateImageEditor(100)
        editor2 = self.generateImageEditor(100)
        editor3 = self.generateImageEditor(100)
    
        widget = ImageEditorWidget(parent=None, editor=editor)
        
        widget.addImageEditor(editor)
        widget.addImageEditor(editor2,(0,1))
        widget.addImageEditor(editor3,(0,1))
        
        s.addWidget(widget)
        s.show()

        app.exec_()


    def generateImageEditor(self,dimension=200):
        
        twoDtestVolume1 = TwoDtestVolume(dimension)
        twoDtestVolume2 = TwoDtestVolume(200)
        lower = numpy.floor(1.0*dimension/4.0)
        middel = numpy.floor((1.0*dimension/2.0))
        upper  = numpy.floor((3.0*dimension/4.0))
        a=numpy.random.randint(lower,middel)
        b=numpy.random.randint(middel,upper)
        twoDtestVolume2[a:b,a:b]=120
        source1 = ArraySource(twoDtestVolume1)
        source2 = ArraySource(twoDtestVolume2)
        layerstack = LayerStackModel()
        layerstack.append(GrayscaleLayer(source1))
        layerstack.append(GrayscaleLayer(source2))
        shape = source1._array.shape
        editor = ImageEditor(layerstack)
        editor.dataShape = shape
        return editor
    
        

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import sys
    import signal   
    signal.signal(signal.SIGINT, signal.SIG_DFL)
        
     
    
    testies = testWidget()
    
        


        
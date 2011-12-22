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
                        QSizePolicy, QVBoxLayout
from imageEditorComponents import ImageViewWidget, PositionStatusBar2D,\
                                  PositionModelImage
from pixelpipeline.datasources import ArraySource
from imageEditor import ImageEditor
from volumina.layer import GrayscaleLayer
from volumina.layerstack import LayerStackModel
from testing import TwoDtestVolume
import numpy,sys
from functools import partial



#*******************************************************************************
# I m a g e E d i t o r W i d g e t                                            *
#*******************************************************************************

class ImageEditorWidget(QWidget):
    def __init__( self, parent=None, editor=None ):
        super(ImageEditorWidget, self).__init__(parent=parent)
        
        self._imageEditor = editor
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("QWidget { background-color: rgb(0, 255,\
255); }")
        if self._imageEditor != None:
            self.init(self._imageEditor)
    
    def init(self, imageEditor):

        self._imageEditor = imageEditor
        
        imageViewWigdet = ImageViewWidget(self, imageEditor.imageView[0])
        
        positionStatusbar2D = PositionStatusBar2D()
        positionStatusbar2D.create(\
            QColor("green"), QColor("white"), \
            QColor("blue"), QColor("white"), \
            QColor("gray"), QColor("white") \
        )
        
        def onPosModelChanged(positionStatusBar2D, oldPosModel, newPosModel):
            if oldPosModel:
                oldPosModel.cursorPositionChanged.disconnect(positionStatusbar2D.updateCoordLabels)
            self._imageEditor.posModel.cursorPositionChanged.connect(positionStatusbar2D.updateCoordLabels)
        
        self._imageEditor.posModelChanged.connect(partial(onPosModelChanged, positionStatusbar2D))
        imageViewWigdet.addStatusBar(positionStatusbar2D)
        
        
        self.layout.addWidget(imageViewWigdet)
        
class TestWidget(object):
    
    def __init__(self):
        
        super(TestWidget,self).__init__()
        
    def makeWidget(self):
        editor = self.generateImageEditor()
        widget = ImageEditorWidget(parent=None,editor=editor)
        return widget
        
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

    
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #make the program quit on Ctrl+C

    import signal   
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    test = TestWidget()
    widget = test.makeWidget()
    widget.show()
    app.exec_()
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
from PyQt4.QtGui import QApplication, QWidget, QSplitter, QHBoxLayout, QColor,\
                        QSizePolicy
from imageEditorComponents import ImageViewWidget, PositionStatusBar2D
from pixelpipeline.datasources import ArraySource
from imageEditor import ImageEditor



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

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)        
        self.setLayout(self.layout)
        
       
        self.imageViewWigdet = ImageViewWidget(self, self._ie.imageView[0])
        self.positionStatusbar2D = PositionStatusBar2D()
        self.positionStatusbar2D.create(\
            QColor("green"), QColor("white"), \
            QColor("blue"), QColor("white"),  \
            QColor("gray"), QColor("white") \
        )
        self.imageViewWigdet.addStatusBar(self.positionStatusbar2D)
        self.layout.addWidget(self.imageViewWigdet)

        self._ie.posModel.cursorPositionChanged.connect(self._updateInfoLabels)
        
        self.updateGeometry()
        self.update()
        self.imageViewWigdet.update()        

    def _updateInfoLabels(self, pos):
        self.positionStatusbar2D.setMouseCoords(*pos)
             
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import sys
    import signal   
    
    signal.signal(signal.SIGINT, signal.SIG_DFL)
   
    from volumina.layer import GrayscaleLayer
    from volumina.layerstack import LayerStackModel
    from testing import TwoDtestVolume
    
    app = QApplication(sys.argv)
    
    s = QSplitter()
    
    twoDtestVolume1 = TwoDtestVolume(200)
    twoDtestVolume2 = TwoDtestVolume(200)
    twoDtestVolume2[75:125,75:125]=0
    source1 = ArraySource(twoDtestVolume1)
    source2 = ArraySource(twoDtestVolume2)
    layerstack = LayerStackModel()
    layerstack.append(GrayscaleLayer(source1))
    layerstack.append(GrayscaleLayer(source2))
    shape = source1._array.shape
    editor = ImageEditor(shape,layerstack)
    
    
    widget = ImageEditorWidget(parent=None, editor=editor)


    s.addWidget(widget)
    s.show()

    app.exec_()

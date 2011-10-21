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
from singlesplitter import SingleView, SingleStatusBar
from pixelpipeline.datasources import ArraySource
from imageEditor import ImageEditor


#*******************************************************************************
# I m a g e E d i t o r W i d g e t                                            *
#*******************************************************************************

class ImageEditorWidget(QWidget):
    def __init__( self, parent=None, editor=None ):
        super(ImageEditorWidget, self).__init__(parent=parent)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.StrongFocus)
        
        if editor!=None:
            self.init(editor)
    
    def init(self, imageEditor):

        self._ie = imageEditor

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)        
        self.setLayout(self.layout)
        
        self.singleview = SingleView(self, self._ie.imageView)
        self.singleviewStatusBar = SingleStatusBar()
        self.singleviewStatusBar.createSingleStatusBar(QColor("green"), QColor("white"), QColor("blue"), QColor("white"), QColor("gray"), QColor("white"))
        self.singleview.addStatusBar(self.singleviewStatusBar)
        self.layout.addWidget(self.singleview)

        self._ie.posModel.cursorPositionChanged.connect(self._updateInfoLabels)
        
        self.updateGeometry()
        self.update()
        self.singleview.update()        

    def _updateInfoLabels(self, pos):
        self.singleviewStatusBar.setMouseCoords(*pos)
             
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
    
    twoDtestVolume = TwoDtestVolume(200)
    source = ArraySource(twoDtestVolume)
    layerstack = LayerStackModel()
    layerstack.append(GrayscaleLayer(source)) 
    shape = source._array.shape
    #editor = ImageEditor(shape, layerstack)
    editor = ImageEditor(None,None,twoDtestVolume)
    
    
    widget = ImageEditorWidget(parent=None, editor=editor)


    s.addWidget(widget)
    
    s.showMaximized()

    app.exec_()

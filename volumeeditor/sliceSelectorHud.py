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
from PyQt4.QtGui import QFrame, QHBoxLayout, QSpinBox, QSizePolicy, QLabel, \
                        QAbstractSpinBox, QColor, QPalette

#*******************************************************************************
# S l i c e S e l e c t o r H u d                                              *
#*******************************************************************************

class SliceSelectorHud(QFrame):
    @property
    def maximum(): return self._maximum
    @property
    def minimum(): return self._minimum
    @maximum.setter
    def maximum(self, m):
        self._maximum = m
        self.coordLabel.setText("of %d" % self._maximum)
        self.sliceSelector.setRange(self._minimum, self._maximum)
    @minimum.setter
    def minimum(self, m):
        self._minimum = m
        self.sliceSelector.setRange(self._minimum, self._maximum)
    @property
    def label(self):
        return self._label
    @label.setter
    def label(self, l):
        self._label = l
        self.dimLabel.setText(l)
    
    @property
    def bgColor(self):
        return self._bgColor
    @bgColor.setter
    def bgColor(self, color):
        self._bgColor = color
        palette = self.palette();
        palette.setColor(self.backgroundRole(), color);
        self.setAutoFillBackground(True);
        self.setPalette(palette)
    
    def __init__(self, parent = None):
        super(SliceSelectorHud, self).__init__(parent)

        # init properties
        self._minimum = 0
        self._maximum = 1
        self._label   = ''
        self._bgColor = QColor(255,255,255)

        # configure self
        #
        # a border-radius of >0px to make the Hud appear rounded
        # does not work together with an QGLWidget, the corners just appear black
        # instead of transparent
        #self.setStyleSheet("QFrame {background-color: white; color: black; border-radius: 0px;}")
        
        
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(3,1,3,1)

        # dimension label
        self.dimLabel = QLabel(self)
        font = self.dimLabel.font()
        font.setBold(True)
        self.dimLabel.setFont(font)
        self.layout().addWidget(self.dimLabel)

        # coordinate selection
        self.sliceSelector = QSpinBox()
        self.sliceSelector.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sliceSelector.setAlignment(Qt.AlignRight)
        self.sliceSelector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)            
        self.layout().addWidget(self.sliceSelector)

        # coordinate label
        self.coordLabel = QLabel()
        self.layout().addWidget(self.coordLabel)

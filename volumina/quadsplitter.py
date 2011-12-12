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

from PyQt4.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt4.QtGui import QSizePolicy, QWidget, QVBoxLayout, QSplitter
            
class ImageView2DFloatingWindow(QWidget):
    onCloseClick = pyqtSignal()
    def __init__(self):
        QWidget.__init__(self)
        
    def closeEvent(self, event):
        self.onCloseClick.emit()
        event.ignore()

class ImageView2DDockWidget(QWidget):
    onDockButtonClicked = pyqtSignal()
    onMaxButtonClicked = pyqtSignal()
    onMinButtonClicked = pyqtSignal()
    def __init__(self, graphicsView):
        QWidget.__init__(self)
        
        self.graphicsView = graphicsView
        self._isDocked = True
        self._isMaximized = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.windowForGraphicsView = ImageView2DFloatingWindow()
        self.windowForGraphicsView.layout = QVBoxLayout()
        self.windowForGraphicsView.layout.setContentsMargins(0, 0, 0, 0)
        self.windowForGraphicsView.setLayout(self.windowForGraphicsView.layout)
        
        self.windowForGraphicsView.onCloseClick.connect(self.onDockButton)
    
        self.addGraphicsView()
    
    def connectHud(self):
        if hasattr(self.graphicsView, '_hud'):
            self.graphicsView._hud.dockButtonClicked.connect(self.onDockButton)
            self.graphicsView._hud.maximizeButtonClicked.connect(self.onMaxButton)
        
    def onMaxButton(self):
        if self._isMaximized:
            self.onMinButtonClicked.emit()
            self.minimizeView()
        else:
            self.onMaxButtonClicked.emit()
            self.maximizeView()
        
    def onDockButton(self):
        self.onDockButtonClicked.emit()
        
    def addGraphicsView(self):
        self.layout.addWidget(self.graphicsView)
        
    def removeGraphicsView(self):
        self.layout.removeWidget(self.graphicsView)
        
    def undockView(self):
        self._isDocked = False
        self.graphicsView._hud.dockButton.setDockIcon()
        self.graphicsView._hud.maxButton.setEnabled(False)
        
        self.removeGraphicsView()
        self.windowForGraphicsView.layout.addWidget(self.graphicsView)
        self.windowForGraphicsView.show()
        self.windowForGraphicsView.raise_()
    
    def dockView(self):
        self._isDocked = True
        self.graphicsView._hud.dockButton.setUndockIcon()
        self.graphicsView._hud.maxButton.setEnabled(True)
        
        self.windowForGraphicsView.layout.removeWidget(self.graphicsView)
        self.windowForGraphicsView.hide()
        self.addGraphicsView()
        
    def maximizeView(self):
        self._isMaximized = True
        self.graphicsView._hud.maxButton.setMinimizeIcon()
        
    def minimizeView(self):
        self._isMaximized = False
        self.graphicsView._hud.maxButton.setMaximizeIcon()



class QuadView(QWidget):
    def __init__(self, parent, view1, view2, view3, view4 = None):
        QWidget.__init__(self, parent)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.installEventFilter(self)
        
        self.dockableContainer = []
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(0)
        
        self.splitVertical = QSplitter(Qt.Vertical, self)
        self.layout.addWidget(self.splitVertical)
        self.splitHorizontal1 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal1.setObjectName("splitter1")
        self.splitHorizontal2 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal2.setObjectName("splitter2")
        self.splitHorizontal1.splitterMoved.connect(self.horizontalSplitterMoved)
        self.splitHorizontal2.splitterMoved.connect(self.horizontalSplitterMoved)
        
        self.imageView2D_1 = view1
        
        self.imageView2D_2 = view2
        
        self.imageView2D_3 = view3
        
        self.testView4 = ImageView2DDockWidget(view4)
        
        self.dock1_ofSplitHorizontal1 = ImageView2DDockWidget(self.imageView2D_1)
        self.dock1_ofSplitHorizontal1.connectHud()
        self.dockableContainer.append(self.dock1_ofSplitHorizontal1)
        self.dock1_ofSplitHorizontal1.onDockButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal1 : self.on_dock(arg))
        self.dock1_ofSplitHorizontal1.onMaxButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal1 : self.on_max(arg))
        self.dock1_ofSplitHorizontal1.onMinButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal1 : self.on_min(arg))

        self.splitHorizontal1.addWidget(self.dock1_ofSplitHorizontal1)
        self.dock2_ofSplitHorizontal1 = ImageView2DDockWidget(self.imageView2D_2)
        self.dock2_ofSplitHorizontal1.onDockButtonClicked.connect(lambda arg=self.dock2_ofSplitHorizontal1 : self.on_dock(arg))
        self.dock2_ofSplitHorizontal1.onMaxButtonClicked.connect(lambda arg=self.dock2_ofSplitHorizontal1 : self.on_max(arg))
        self.dock2_ofSplitHorizontal1.onMinButtonClicked.connect(lambda arg=self.dock2_ofSplitHorizontal1 : self.on_min(arg))
        self.dock2_ofSplitHorizontal1.connectHud()
        self.dockableContainer.append(self.dock2_ofSplitHorizontal1)

        self.splitHorizontal1.addWidget(self.dock2_ofSplitHorizontal1)
        self.dock1_ofSplitHorizontal2 = ImageView2DDockWidget(self.imageView2D_3)
        self.dock1_ofSplitHorizontal2.onDockButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal2 : self.on_dock(arg))
        self.dock1_ofSplitHorizontal2.onMaxButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal2 : self.on_max(arg))
        self.dock1_ofSplitHorizontal2.onMinButtonClicked.connect(lambda arg=self.dock1_ofSplitHorizontal2 : self.on_min(arg))
        self.dock1_ofSplitHorizontal2.connectHud()
        self.dockableContainer.append(self.dock1_ofSplitHorizontal2)
        self.splitHorizontal2.addWidget(self.dock1_ofSplitHorizontal2)
        self.dock2_ofSplitHorizontal2 = ImageView2DDockWidget(self.testView4)
        self.dockableContainer.append(self.dock2_ofSplitHorizontal2)

        self.splitHorizontal2.addWidget(self.dock2_ofSplitHorizontal2)  
        
        #this is a hack: with 0 ms it does not work...
        QTimer.singleShot(250, self._resizeEqual)
    
    def _resizeEqual(self):
        w, h = self.size().width()-self.splitHorizontal1.handleWidth(), self.size().height()-self.splitVertical.handleWidth()
        docks = [self.imageView2D_1, self.imageView2D_2, self.imageView2D_3, self.testView4]
        
        w1  = [docks[i].minimumSize().width() for i in [0,2] ]
        w2  = [docks[i].minimumSize().width() for i in [1,3] ]
        wLeft  = max(w1)
        wRight = max(w2)
        if wLeft > wRight and wLeft > w/2:
            wRight = w - wLeft
        elif wRight >= wLeft and wRight > w/2:
            wLeft = w - wRight
        else:
            wLeft = w/2
            wRight = w/2
        self.splitHorizontal1.setSizes([wLeft, wRight])
        self.splitHorizontal2.setSizes([wLeft, wRight])
        self.splitVertical.setSizes([h/2, h/2])
            
    def eventFilter(self, obj, event):
        if(event.type()==QEvent.WindowActivate):
            self._synchronizeSplitter()
        return False
                
    def _synchronizeSplitter(self):
        sizes1 = self.splitHorizontal1.sizes()
        sizes2 = self.splitHorizontal2.sizes()        
        if sizes1[0] > sizes2[0]:
            self.splitHorizontal1.setSizes(sizes2)
        else:
            self.splitHorizontal2.setSizes(sizes1) 
    
    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self._synchronizeSplitter()
    
    def horizontalSplitterMoved(self, x, y):
        sizes = self.splitHorizontal1.sizes()
        #What. Nr2
        if self.splitHorizontal2.closestLegalPosition(x, y) < self.splitHorizontal2.closestLegalPosition(x, y):
            sizeLeft = self.splitHorizontal1.closestLegalPosition(x, y)
        else:
            sizeLeft = self.splitHorizontal2.closestLegalPosition(x, y)
            
        sizeRight = sizes[0] + sizes[1] - sizeLeft
        sizes = [sizeLeft, sizeRight]
        
        self.splitHorizontal1.setSizes(sizes)
        self.splitHorizontal2.setSizes(sizes) 
        
    def addStatusBar(self, bar):
        self.statusBar = bar
        self.layout.addLayout(self.statusBar)
        
    def setGrayScaleToQuadStatusBar(self, gray):
        self.quadViewStatusBar.setGrayScale(gray)
        
    def setMouseCoordsToQuadStatusBar(self, x, y, z):
        self.quadViewStatusBar.setMouseCoords(x, y, z) 
        
    def on_dock(self, dockWidget):
        if dockWidget._isDocked:
            dockWidget.undockView()
            self.on_min(dockWidget)
            dockWidget.minimizeView()
        else:
            dockWidget.dockView()
   
    def on_max(self, dockWidget):
        for dock in self.dockableContainer:
            if not dockWidget == dock:
                dock.setVisible(False)
                
    def on_min(self, dockWidget):
        for dock in self.dockableContainer:
            if not dockWidget == dock:
                dock.setVisible(True)
    

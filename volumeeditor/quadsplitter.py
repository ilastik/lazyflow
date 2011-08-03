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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import sys

#
# discover icon path
#
from os import path
import resources.icons
_icondir = path.dirname(resources.icons.__file__)

#*******************************************************************************
# D o c k a b l e C o n t a i n e r                                            *
#*******************************************************************************

class DockableContainer(QWidget):
    """
    A widget that can be docked out of a `QuadSplitter` layout.
    """
    
    def __init__(self, number, parent=None):
        QWidget.__init__(self, parent)
        
        self.isDocked = True
        self.replaceWidget = None
        self.mainLayout = None
        self.maximized = False
        
        self.replaceWidget = QWidget(None)
        self.replaceWidget.setObjectName("replaceWidget_%d" % (number))
        
        self.dockButton = QPushButton(None)
        self.dockButton.setObjectName("%d" % (number))
        self.dockButton.setFlat(True)
        self.dockButton.setAutoFillBackground(True)
        self.dockButton.setIcon(QIcon(QPixmap(path.join(_icondir, 'arrow_up.png'))))
        self.dockButton.setIconSize(QSize(10,10));
        self.dockButton.setFixedSize(10,10)
        self.dockButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.maximizeButton = QPushButton(None)
        self.maximizeButton.setObjectName("%d" % (number))
        self.maximizeButton.setFlat(True)
        self.maximizeButton.setAutoFillBackground(True)
        self.maximizeButton.setIcon(QIcon(QPixmap(path.join(_icondir, 'maximize.png'))))
        self.maximizeButton.setIconSize(QSize(10,10));
        self.maximizeButton.setFixedSize(10,10)
        self.maximizeButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        h = QHBoxLayout(None)
        h.setMargin(0); h.setSpacing(0)
        h.addStretch()
        h.addWidget(self.maximizeButton)
        h.addWidget(self.dockButton)
        
        self.mainLayout = QVBoxLayout(None)
        self.mainLayout.setMargin(0); self.mainLayout.setSpacing(0)
        self.mainLayout.addItem(h)
        
        self.mainWidget = QTextEdit(None); self.mainWidget.setDocument(QTextDocument("MAIN widget %d" % (number)))
        self.mainLayout.addWidget(self.mainWidget)
        
        self.setLayout(self.mainLayout)
        
        self.connect(self.dockButton, SIGNAL('clicked()'), self.__onDockButtonClicked )
        self.connect(self.maximizeButton, SIGNAL('clicked()'), self.__onMaximizeButtonClicked )
    
    def __del__(self):
        if not self.isDocked:
            del self
    
    def __onMaximizeButtonClicked(self):
        self.maximized = not self.maximized
        self.dockButton.setEnabled(not self.maximized)
        self.emit(SIGNAL('maximize(bool)'), self.maximized)
    
    def __onDockButtonClicked(self):
        self.setDocked(not self.isDocked)
    
    def setDocked(self, docked):
        if docked:
            self.dockButton.setIcon(QIcon(QPixmap(path.join(_icondir, 'arrow_up.png'))))
        else:
            self.dockButton.setIcon(QIcon(QPixmap(path.join(_icondir, 'arrow_down.png'))))
        
        if not docked:
            self.emit(SIGNAL('undock()'))
            widgetSize = self.size()
            self.setParent(None, Qt.Window)
            self.setWindowFlags(Qt.WindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint))
            self.show()
        else:
            self.emit(SIGNAL('dock()'))
            
        self.isDocked = not self.isDocked

#*******************************************************************************
# Q u a d V i e w                                                              *
#*******************************************************************************

class QuadView(QWidget):
    """
    A layout widget that can hold four widgets (top left, top right, bottom left,
    bottom right). A vertical and horizontal splitter can be used to change the
    relative sizes of the grid columns and rows.
    """
      
    def horizontalSplitterMoved(self):
        w, h = self.size().width()-self.splitHorizontal1.handleWidth(), self.size().height()-self.splitVertical.handleWidth()
        
        w1  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [0,2] ]
        w2  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [1,3] ]
        wLeft  = max(w1)
        wRight = max(w2)
        
        if self.sender().objectName() == "splitter1":
            s = self.splitHorizontal1.sizes()
            if s[0] < wLeft or s[1] < wRight:
                self.splitHorizontal1.setSizes(self.splitHorizontal2.sizes())
            else:
                self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )

        if self.sender().objectName() == "splitter2":
            s = self.splitHorizontal2.sizes()
            if s[0] < wLeft or s[1] < wRight:
                self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )
            else:
                self.splitHorizontal1.setSizes( self.splitHorizontal2.sizes() )
    
    def addWidget(self, i, widget):
        assert 0 <= i < 4, "range of i"
        
        w = self.dockableContainer[i]
        oldMainWidget = w.mainWidget
        w.mainWidget = widget
        oldMainWidget.setParent(None); del oldMainWidget
        w.mainLayout.addWidget(w.mainWidget)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self.dockButton        = 4*[None]
        self.dockableContainer = 4*[None]
        self.firstTime = True
        self.maximized = False

        #split up <-> down
        self.splitVertical    = QSplitter(Qt.Vertical, self)
        self.splitVertical.setChildrenCollapsible(False)
        #split left <-> right
        self.splitHorizontal1 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal1.setChildrenCollapsible(False)
        self.splitHorizontal1.setObjectName("splitter1")
        self.splitHorizontal2 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal2.setObjectName("splitter2")
        self.splitHorizontal2.setChildrenCollapsible(False)
        
        for i in range(4):
            if i<2:
                self.dockableContainer[i] = DockableContainer(i, self.splitHorizontal1)
            else:
                self.dockableContainer[i] = DockableContainer(i, self.splitHorizontal2)
            self.dockableContainer[i].setObjectName("%d" % (i))
            self.connect(self.dockableContainer[i], SIGNAL('dock()'), self.dockContainer )
            self.connect(self.dockableContainer[i], SIGNAL('undock()'), self.undockContainer )
            self.connect(self.dockableContainer[i], SIGNAL('maximize(bool)'), self.maximizeContainer )
        
        self.layout = QVBoxLayout()
        self.layout.setMargin(0); self.layout.setSpacing(0)
        self.layout.addWidget(self.splitVertical)
        self.setLayout(self.layout)
        
        self.connect( self.splitHorizontal1, SIGNAL( 'splitterMoved( int, int )'), self.horizontalSplitterMoved)
        self.connect( self.splitHorizontal2, SIGNAL( 'splitterMoved( int, int )'), self.horizontalSplitterMoved)

    def __del__(self):
        for i in range(4):
            if not self.dockableContainer[i]:
                del self.dockableContainer[i]

    def setMaximized(self, maximized, i):
        if maximized:
            self.splitVertical.setParent(None)
            self.layout.addWidget(self.dockableContainer[i])
        else:
            for i in range(4):
                self.dockableContainer[i].setParent(None)
            for i in range(4):
                if i<2:
                    self.dockableContainer[i].setParent(self.splitHorizontal1)
                else:
                    self.dockableContainer[i].setParent(self.splitHorizontal2)
            self.layout.addWidget(self.splitVertical)
            self.__resizeEqual()
        self.maximized = maximized
    
    def toggleMaximized(self, i):
        self.setMaximized(not self.maximized, i)
    
    def maximizeContainer(self, maximized):
        i = int(self.sender().objectName())
        self.setMaximized(maximized, i)
    
    def deleteUndocked(self):
        toDelete = []
        for i in range(4):
            if not self.dockableContainer[i].isDocked:
                toDelete.append( self.dockableContainer[i] )
        for x in toDelete: x.deleteLater()

    def resizeEvent(self, event):
        if self.firstTime:
            self.__resizeEqual()
            self.firstTime=False
    
    def __resizeEqual(self):
        w, h = self.size().width()-self.splitHorizontal1.handleWidth(), self.size().height()-self.splitVertical.handleWidth()
        
        w1  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [0,2] ]
        w2  = [self.dockableContainer[i].mainLayout.minimumSize().width() for i in [1,3] ]
        wLeft  = max(w1)
        wRight = max(w2)
        if wLeft > wRight and wLeft > w/2:
            wRight = w - wLeft
        elif wRight >= wLeft and wRight > w/2:
            wLeft = w - wRight
        else:
            wLeft = w/2
            wRight = w/2
        self.splitHorizontal1.setSizes([wLeft, wRight+10])
        self.splitHorizontal2.setSizes([wLeft, wRight+10])
        self.splitVertical.setSizes([h/2, h/2])
    
    def undockContainer(self):
        i = int(self.sender().objectName())
        w = self.dockableContainer[i]
        
        index = i
        splitter = self.splitHorizontal1
        if i>=2:
            index = i-2
            splitter = self.splitHorizontal2
        assert 0 <= index < 2
    
        size = w.size()
        splitter.widget(index).setParent(None)
        w.replaceWidget.resize(size)
        splitter.insertWidget(index, w.replaceWidget)
        
        if i<2:
            self.splitHorizontal2.setSizes( self.splitHorizontal1.sizes() )
        else:
            self.splitHorizontal1.setSizes( self.splitHorizontal2.sizes() )
            
    def dockContainer(self):
        i = int(self.sender().objectName())
        w = self.dockableContainer[i]
        assert not w.isDocked

        index = i
        splitter = self.splitHorizontal1
        if i>=2:
            index = i-2
            splitter = self.splitHorizontal2
        assert 0 <= index < 2

        splitter.widget(index).setParent(None)
        if i<2:
            self.splitHorizontal1.insertWidget(index, w)
        else:
            self.splitHorizontal2.insertWidget(index, w)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)

    class Window(QMainWindow):
        def __init__(self):
            QMainWindow.__init__(self)
            #self.setAttribute(Qt.WA_DeleteOnClose)
            
            widget= QWidget()
            mainLayout = QVBoxLayout()
            mainLayout.setMargin(0); mainLayout.setSpacing(0)
            self.q = QuadView(self)
            
            for i in range(4):
                edit = QTextEdit()
                edit.setDocument(QTextDocument("view %d" % (i)))
                edit.setMinimumSize(200+100*i,200+100*i)
                self.q.addWidget(i, edit)
            
            mainLayout.addWidget(self.q)
            self.setCentralWidget(widget)
            widget.setLayout(mainLayout)
        
        def closeEvent(self, event):
            self.q.deleteUndocked()
            self.deleteLater()

    window = Window()
    window.show()
    app.exec_()

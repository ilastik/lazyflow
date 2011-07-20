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

# TODO
# TODO
# TODO
# port the following revisions:
#    1f810747c21380eda916c2c5b7b5d1893f92663e
#    e65f5bad2cd9fdaefbe7ceaafa0cce0e071b56e4

from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QApplication, QWidget, QLabel, QSpinBox, \
                        QShortcut, QKeySequence, QSplitter, \
                        QVBoxLayout, QHBoxLayout, QPushButton, QToolButton

import numpy, copy
from functools import partial

from quadsplitter import QuadView
from view3d.view3d import OverviewScene
      
from sliceSelectorHud import SliceSelectorHud
from positionModel import PositionModel
from navigationControler import NavigationControler, NavigationInterpreter

from volumeEditor import VolumeEditor

class VolumeEditorWidget(QWidget):
    def __init__( self, volumeeditor, parent=None ):
        super(VolumeEditorWidget, self).__init__(parent=parent)
        self._ve = volumeeditor

        self.setFocusPolicy(Qt.StrongFocus)

        # setup quadview
        self.quadview = QuadView(self)
        self.quadview.addWidget(0, self._ve.imageViews[2])
        self.quadview.addWidget(1, self._ve.imageViews[0])
        self.quadview.addWidget(2, self._ve.imageViews[1])

        #3d overview
        self.overview = OverviewScene(self, self._ve._shape[1:4])
        self.quadview.addWidget(3, self.overview)
        #FIXME: resurrect        
        #self.overview.changedSlice.connect(self.changeSlice)
        self._ve.changedSlice.connect(self.overview.ChangeSlice)

        # layout
        viewingLayout = QVBoxLayout()
        viewingLayout.setContentsMargins(10,2,0,2)
        viewingLayout.setSpacing(0)
        viewingLayout.addWidget(self.quadview)
        self.quadview.setContentsMargins(0,0,10,0)

        # Label below views
        labelLayout = QHBoxLayout()
        labelLayout.setMargin(0)
        labelLayout.setSpacing(5)
        labelLayout.setContentsMargins(0,0,0,0)
        self.posLabel = QLabel()
        self.pixelValuesLabel = QLabel()
        labelLayout.addWidget(self.posLabel)
        labelLayout.addWidget(self.pixelValuesLabel)
        labelLayout.addStretch()
        viewingLayout.addLayout(labelLayout)

        # Right side toolbox
        self._toolBox = QWidget()
        self._toolBoxLayout = QVBoxLayout()
        self._toolBoxLayout.setMargin(5)
        self._toolBox.setLayout(self._toolBoxLayout)
        self._toolBoxLayout.addStretch()

        # Toggle slice intersection marks
        self.indicateSliceIntersectionButton = QToolButton()
        self.indicateSliceIntersectionButton.setText("Indicate Current Position")
        self.indicateSliceIntersectionButton.setCheckable(True)
        self.indicateSliceIntersectionButton.setChecked(True)        
        self._toolBoxLayout.addWidget(self.indicateSliceIntersectionButton)

        # Channel Selector QComboBox in right side tool box
        self._channelSpin = QSpinBox()
        self._channelSpin.setEnabled(True)
        
        #FIXME: resurrect
        #self.channelEditBtn = QPushButton('Edit channels')
        #self.channelEditBtn.clicked.connect(self._ve.on_editChannels)
        
        channelLayout = QHBoxLayout()
        channelLayout.addWidget(self._channelSpin)
        #channelLayout.addWidget(self.channelEditBtn) #FIXME: resurrect
        
        self._channelSpinLabel = QLabel("Channel:")
        self._toolBoxLayout.addWidget(self._channelSpinLabel)
        self._toolBoxLayout.addLayout(channelLayout)
        self._toolBoxLayout.setAlignment(Qt.AlignTop)

        # == 3 checks for RGB image and activates channel selector
        if self._ve._shape[-1] == 1 or self._ve._shape[-1] == 3: #only show when needed
            self._channelSpin.setVisible(False)
            self._channelSpinLabel.setVisible(False)
            #self.channelEditBtn.setVisible(False)
        self._channelSpin.setRange(0,self._ve._shape[-1] - 1)
        def setChannel(c):
            self._ve.posModel.channel = c
        self._channelSpin.valueChanged.connect(setChannel)

        # setup the layout for display
        self.splitter = QSplitter()
        self.splitter.setContentsMargins(0,0,0,0)
        tempWidget = QWidget()
        tempWidget.setLayout(viewingLayout)
        self.splitter.addWidget(tempWidget)
        self.splitter.addWidget(self._toolBox)
        splitterLayout = QVBoxLayout()
        splitterLayout.setMargin(0)
        splitterLayout.setSpacing(0)
        splitterLayout.addWidget(self.splitter)
        self.setLayout(splitterLayout)

        # drawing
        axisLabels = ["X:", "Y:", "Z:"]
        for i, v in enumerate(self._ve.imageViews):
            v.beginDraw.connect(partial(self._ve.beginDraw, axis=i))
            v.endDraw.connect(partial(self._ve.endDraw, axis=i))
            v.hud = SliceSelectorHud()
            #connect interpreter
            v.hud.sliceSelector.valueChanged.connect(partial(self._ve.navInterpret.changeSliceAbsolute, axis=i))
            #hud
            v.hud.bgColor = self._ve.navCtrl.axisColors[i] #FIXME
            v.hud.label = axisLabels[i]
            v.hud.minimum = 0
            v.hud.maximum = self._ve.posModel.volumeExtent(i)

        def toggleSliceIntersection(state):
            self._ve.navCtrl.indicateSliceIntersection = state
        self.indicateSliceIntersectionButton.toggled.connect(toggleSliceIntersection)

        self._ve.posModel.cursorPositionChanged.connect(self._updateInfoLabels)

        # shortcuts
        self._initShortcuts()

        
        self.updateGeometry()
        self.update()
        self.quadview.update()

    def _shortcutHelper(self, keySequence, group, description, parent, function, context = None, enabled = None):
        shortcut = QShortcut(QKeySequence(keySequence), parent, member=function, ambiguousMember=function)
        if context != None:
            shortcut.setContext(context)
        if enabled != None:
            shortcut.setEnabled(True)
        return shortcut, group, description

    def _initShortcuts(self):
        self.shortcuts = []
        self.shortcuts.append(self._shortcutHelper("Ctrl+Z", "Labeling", "History undo", self, self._ve.historyUndo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Z", "Labeling", "History redo", self, self._ve.historyRedo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Ctrl+Y", "Labeling", "History redo", self, self._ve.historyRedo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Space", "Overlays", "Invert overlay visibility", self, self._ve.toggleOverlays, enabled = True))
        self.shortcuts.append(self._shortcutHelper("l", "Labeling", "Go to next label (cyclic, forward)", self, self._ve.nextLabel))
        self.shortcuts.append(self._shortcutHelper("k", "Labeling", "Go to previous label (cyclic, backwards)", self, self._ve.prevLabel))
        
        def fullscreenView(axis):
            m = not self.quadview.maximized
            print "maximize axis=%d = %r" % (axis, m)
            self.quadview.setMaximized(m, axis)
        
        self.shortcuts.append(self._shortcutHelper("q", "Navigation", "Switch to next channel", self, self._ve.nextChannel))
        self.shortcuts.append(self._shortcutHelper("a", "Navigation", "Switch to previous channel", self, self._ve.previousChannel))
        
        maximizeShortcuts = ['x', 'y', 'z']
        maximizeViews     = [1,   2,     0]
        for i, v in enumerate(self._ve.imageViews):
            self.shortcuts.append(self._shortcutHelper(maximizeShortcuts[i], "Navigation", \
                                  "Enlarge slice view %s to full size" % maximizeShortcuts[i], \
                                  self, partial(fullscreenView, maximizeViews[i]), Qt.WidgetShortcut))
            
            self.shortcuts.append(self._shortcutHelper("n", "Labeling", "Increase brush size", v,self._ve._drawManager.brushSmaller, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("m", "Labeling", "Decrease brush size", v, self._ve._drawManager.brushBigger, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("+", "Navigation", "Zoom in", v,  v.zoomIn, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("-", "Navigation", "Zoom out", v, v.zoomOut, Qt.WidgetShortcut))
            
            def sliceDelta(axis, delta):
                newPos = copy.copy(self._ve.posModel.slicingPos)
                newPos[axis] += delta
                self._ve.posModel.slicingPos = newPos
            self.shortcuts.append(self._shortcutHelper("p", "Navigation", "Slice up",   v, partial(sliceDelta, i, 1),  Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("o", "Navigation", "Slice down", v, partial(sliceDelta, i, -1), Qt.WidgetShortcut))
            
            self.shortcuts.append(self._shortcutHelper("Ctrl+Up",   "Navigation", "Slice up",   v, partial(sliceDelta, i, 1),  Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Down", "Navigation", "Slice down", v, partial(sliceDelta, i, -1), Qt.WidgetShortcut))
            
            self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Up",   "Navigation", "10 slices up",   v, partial(sliceDelta, i, 10),  Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Down", "Navigation", "10 slices down", v, partial(sliceDelta, i, -10), Qt.WidgetShortcut))

    def _updateInfoLabels(self, pos):
        for i in range(3):
            if pos[i] < 0 or pos[i] >= self._ve.posModel.shape[i]:
                self._ve.posLabel.setText("")
                return
                                
        rawRef = self._ve.overlayWidget.getOverlayRef("Raw Data")
        colorValues = rawRef._data[0,pos[0], pos[1], pos[2], 0]
        
        self.posLabel.setText("<b>x:</b> %03i  <b>y:</b> %03i  <b>z:</b> %03i" % (pos[0], pos[1], pos[2]))
        
        #FIXME RGB is a special case only
        if isinstance(colorValues, numpy.ndarray):
            self.pixelValuesLabel.setText("<b>R:</b> %03i  <b>G:</b> %03i  <b>B:</b> %03i" % (colorValues[0], colorValues[1], colorValues[2]))
        else:
            self.pixelValuesLabel.setText("<b>Gray:</b> %03i" %int(colorValues))
            
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    import os, sys
    from PyQt4.QtCore import QObject, QRectF, QTimer

    from PyQt4.QtGui import QColor
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from overlayItem  import OverlayItem  
    from _testing.volume import DataAccessor
    
    def img(N):
        def meshgrid2(*arrs):
            arrs = tuple(reversed(arrs))  #edit
            lens = map(len, arrs)
            dim = len(arrs)

            sz = 1
            for s in lens:
                sz*=s

            ans = []    
            for i, arr in enumerate(arrs):
                slc = [1]*dim
                slc[i] = lens[i]
                arr2 = numpy.asarray(arr).reshape(slc)
                for j, sz in enumerate(lens):
                    if j!=i:
                        arr2 = arr2.repeat(sz, axis=j) 
                ans.append(arr2)

            return tuple(ans)

        N2 = N/2

        X,Y,Z = meshgrid2(numpy.arange(N),numpy.arange(N),numpy.arange(N))

        s = numpy.zeros((N,N,N))
        s[:] = 255

        s[(X-10)**2+(Y-10)**2+(Z-15)**2 < (N2-2)**2] = 0

        s[(X-30)**2+(Y-30)**2+(Z-30)**2 < (10)**2] = 128

        s[0:10,0:10,0:10] = 200
        
        return s
    
    class Test(QObject):
        def __init__(self, useGL, argv):
            QObject.__init__(self)
            
            from testing import stripes
            
            if "hugeslab" in argv:
                N = 2000
                self.data = (numpy.random.rand(N,2*N, 10)*255).astype(numpy.uint8)
            elif "5d" in argv:
                file = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d-5-213-202-13-2.npy"
                print "loading file '%s'" % file
                self.data = numpy.load(file)
                self.data = self.data.astype(numpy.uint16)
                print "...done"
            elif "cuboid" in argv:
                N = 100
                from testing import testVolume
                self.data = testVolume(N)
            elif "stripes" in argv:
                self.data = stripes(50,35,20)
            else:
                raise RuntimeError("Invalid testing mode")
            
            class FakeOverlayWidget(QWidget):
                selectedOverlay = pyqtSignal(int)
                def __init__(self):
                    QWidget.__init__(self)
                    self.overlays = None
                def getOverlayRef(self, key):
                    return self.overlays[0]            
            overlayWidget = FakeOverlayWidget()
            self.dataOverlay = OverlayItem(DataAccessor(self.data), alpha=1.0, \
                                           color=Qt.black, \
                                           colorTable=OverlayItem.createDefaultColorTable('GRAY', 256), \
                                           autoVisible=True, \
                                           autoAlphaChannel=False)
            overlayWidget.overlays = [self.dataOverlay.getRef()]

            shape = self.data.shape
            if len(self.data.shape) == 3:
                shape = (1,)+self.data.shape+(1,)
            
            self.editor = VolumeEditor(shape, useGL=useGL, overlayWidget=overlayWidget)
            self.editor.setDrawingEnabled(True)            
            self.widget = VolumeEditorWidget( self.editor )
            
            #FIXME: porting
            self.editor.setOverlayWidget(overlayWidget)
            
            self.widget.show()
            
            if not 't' in sys.argv:
                #show some initial position
                self.editor.posModel.slicingPos = [5,10,2]
            else:
                def randomMove():
                    self.editor.posModel.slicingPos = [numpy.random.randint(0,self.data.shape[i]) for i in range(3)]
                t = QTimer(self)
                t.setInterval(1000)
                t.timeout.connect(randomMove)
                t.start()

    app = QApplication(sys.argv)
    
    if len(sys.argv) < 2:
        print "Usage: python volumeeditor.py <testmode> (hugeslab, cuboid, veng)"
        app.quit()
        sys.exit(0)
    
    if 'cuboid' in sys.argv or 'hugeslab' in sys.argv or '5d' in sys.argv:
        s = QSplitter()
        t1 = Test(True, sys.argv)
        t2 = Test(False, sys.argv)
        s.addWidget(t1.widget)
        s.addWidget(t2.widget)

        button=QPushButton("fitToView");
    
        s.addWidget(button)
    
        def fit():
            for i in range(3):
                t1.editor.imageViews[i].changeViewPort(QRectF(0,0,30,30))
                t2.editor.imageViews[i].changeViewPort(QRectF(0,0,30,30))
            
        button.clicked.connect(fit)       
    
        s.showMaximized()

    if 'veng' in sys.argv:
        ve = VolumeEditor()
        frame = VolumeEditorWidget( ve )
        frame.showMaximized()

        ve.addVolume( 0 )
        ve.addVolume( 0 )

    app.exec_()

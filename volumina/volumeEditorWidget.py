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

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QApplication, QWidget, QShortcut, QKeySequence, \
                        QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, \
                        QColor, QSizePolicy

import numpy, copy
from functools import partial

from quadsplitter import QuadView
      
from sliceSelectorHud import imageView2DHud, QuadStatusBar
from pixelpipeline.datasources import ArraySource, LazyflowSinkSource

from volumeEditor import VolumeEditor

#*******************************************************************************
# V o l u m e E d i t o r W i d g e t                                          *
#*******************************************************************************

class VolumeEditorWidget(QWidget):
    def __init__( self, parent=None, editor=None ):
        super(VolumeEditorWidget, self).__init__(parent=parent)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.StrongFocus)
        
        if editor!=None:
            self.init(editor)
    
    def init(self, volumina):
        self._ve = volumina

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(self.layout)
        
        # setup quadview
        axisLabels = ["X", "Y", "Z"]
        axisColors = [QColor("#dc143c"), QColor("green"), QColor("blue")]
        for i, v in enumerate(self._ve.imageViews):
            v.hud = imageView2DHud()
            #connect interpreter
            v.hud.createImageView2DHud(axisLabels[i], self._ve.posModel.volumeExtent(i), axisColors[i], QColor("white"))
            v.hud.sliceSelector.valueChanged.connect(partial(self._ve.navCtrl.changeSliceAbsolute, axis=i))

        self.quadview = QuadView(self, self._ve.imageViews[2], self._ve.imageViews[0], self._ve.imageViews[1], self._ve.view3d)
        self.quadViewStatusBar = QuadStatusBar()
        self.quadViewStatusBar.createQuadViewStatusBar(QColor("#dc143c"), QColor("white"), QColor("green"), QColor("white"), QColor("blue"), QColor("white"), QColor("gray"), QColor("white"))
        self.quadview.addStatusBar(self.quadViewStatusBar)
        self.layout.addWidget(self.quadview)

        self.quadview.statusBar.channelSpinBox.setRange(0,self._ve._shape[-1] - 1)
        self.quadview.statusBar.timeSpinBox.setRange(0,self._ve._shape[0] - 1)
        def setChannel(c):
            print "set channel = %d, posModel has channel = %d" % (c, self._ve.posModel.channel)
            if c == self._ve.posModel.channel:
                return
            self._ve.posModel.channel = c
        self.quadview.statusBar.channelSpinBox.valueChanged.connect(setChannel)
        def getChannel(newC):
            self.quadview.statusBar.channelSpinBox.setValue(newC)
        self._ve.posModel.channelChanged.connect(getChannel)
        def setTime(t):
            print "set channel = %d, posModel has time = %d" % (t, self._ve.posModel.time)
            if t == self._ve.posModel.time:
                return
            self._ve.posModel.time = t
        self.quadview.statusBar.timeSpinBox.valueChanged.connect(setTime)
        def getTime(newT):
            self.quadview.statusBar.timeSpinBox.setValue(newT)
        self._ve.posModel.timeChanged.connect(getTime) 


        def toggleSliceIntersection(state):
            self._ve.navCtrl.indicateSliceIntersection = (state == Qt.Checked)
        self.quadview.statusBar.positionCheckBox.stateChanged.connect(toggleSliceIntersection)

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
        #self.shortcuts.append(self._shortcutHelper("Ctrl+Z", "Labeling", "History undo", self, self._ve.historyUndo, Qt.ApplicationShortcut, True))
        #self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Z", "Labeling", "History redo", self, self._ve.historyRedo, Qt.ApplicationShortcut, True))
        #self.shortcuts.append(self._shortcutHelper("Ctrl+Y", "Labeling", "History redo", self, self._ve.historyRedo, Qt.ApplicationShortcut, True))
        
        def fullscreenView(axis):
            m = not self.quadview.maximized
            print "maximize axis=%d = %r" % (axis, m)
            self.quadview.setMaximized(m, axis)
        
        maximizeShortcuts = ['x', 'y', 'z']
        maximizeViews     = [1,   2,     0]
        for i, v in enumerate(self._ve.imageViews):
            self.shortcuts.append(self._shortcutHelper(maximizeShortcuts[i], "Navigation", \
                                  "Enlarge slice view %s to full size" % maximizeShortcuts[i], \
                                  self, partial(fullscreenView, maximizeViews[i]), Qt.WidgetShortcut))
            
            #self.shortcuts.append(self._shortcutHelper("n", "Labeling", "Increase brush size", v,self._ve._drawManager.brushSmaller, Qt.WidgetShortcut))
            #self.shortcuts.append(self._shortcutHelper("m", "Labeling", "Decrease brush size", v, self._ve._drawManager.brushBigger, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("+", "Navigation", "Zoom in", v,  v.zoomIn, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("-", "Navigation", "Zoom out", v, v.zoomOut, Qt.WidgetShortcut))
            
            self.shortcuts.append(self._shortcutHelper("q", "Navigation", "Switch to next channel",     v, self._ve.nextChannel,     Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("a", "Navigation", "Switch to previous channel", v, self._ve.previousChannel, Qt.WidgetShortcut))
            
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
        self.quadViewStatusBar.setMouseCoords(*pos)
             
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    import os, sys, h5py

    import numpy as np
    from PyQt4.QtCore import QObject, QRectF, QTime
    from PyQt4.QtGui import QColor
    
    from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
    from lazyflow import operators
    from volumina.pixelpipeline.datasources import LazyflowSource, ConstantSource
    from volumina.pixelpipeline._testing import OpDataProvider
    from volumina._testing.from_lazyflow import OpDataProvider5D, OpDelay
    from volumina.layer import GrayscaleLayer, RGBALayer, ColortableLayer
    from volumina.layerwidget.layerwidget import LayerWidget
    from volumina.layerstack import LayerStackModel
    
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
        def __init__(self, argv):
            QObject.__init__(self)
            
            layerstack = LayerStackModel()
            g = Graph()
            
            if "hugeslab" in argv:
                N = 1000
                
                hugeslab = (numpy.random.rand(1,N,2*N, 10,1)*255).astype(numpy.uint8)
                
                op1 = OpDataProvider(g, hugeslab)
                op2 = OpDelay(g, 0.000050)
                op2.inputs["Input"].connect(op1.outputs["Data"])
                source = LazyflowSource(op2.outputs["Output"])
                layers = [GrayscaleLayer( source )]
                
                layerstack.append( GrayscaleLayer( source ) )
                
                print "*** hugeslab has shape = %r" % (hugeslab.shape,)

            elif "5d" in argv:
                file = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
                print "loading file '%s'" % file
                
                op1 = OpDataProvider5D(g, file)
                op2 = OpDelay(g, 0.000003)
                op2.inputs["Input"].connect(op1.outputs["Data5D"])
                source = LazyflowSource(op2.outputs["Output"])
                
                layerstack.append( GrayscaleLayer( source ) )
                
                print "...done"
            elif "cuboid" in argv:
                N = 100
                from testing import testVolume
                source = ArraySource(testVolume(N))
                
                layerstack.append( GrayscaleLayer( source ) )
            
            elif "3dvol" in argv:
                fname = os.path.split(os.path.abspath(__file__))[0] +"/_testing/l.h5"
                if not os.path.exists(fname):
                    print "please run _testin/labeled3d.py to make a l.h5 file"
                    app.quit()
                    sys.exit(1)
                f = h5py.File(fname, 'r')
                d = f["volume/data"]
                print d.shape, d.dtype
                source = ArraySource(d)
                layerstack.append( GrayscaleLayer( source ) )
                
            elif "comp" in argv:
                fn = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
                raw = np.load(fn)
                print "loading file '%s'" % fn

                op1 = OpDataProvider(g, raw[:,:,:,:,0:1]/20)
                op2 = OpDelay(g, 0.00000)
                op2.inputs["Input"].connect(op1.outputs["Data"])
                nucleisrc = LazyflowSource(op2.outputs["Output"])
                op3 = OpDataProvider(g, raw[:,:,:,:,1:2]/10)
                op4 = OpDelay(g, 0.00000)
                op4.inputs["Input"].connect(op3.outputs["Data"])
                membranesrc = LazyflowSource(op4.outputs["Output"])

                layerstack.append( RGBALayer( green = membranesrc, red = nucleisrc ) )
                
                source = nucleisrc

            elif "layers" in argv:
                fn = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
                raw = np.load(fn)
                print "loading file '%s'" % fn
                print "raw data has shape %r", raw.shape

                op1 = OpDataProvider(g, raw[:,:,:,:,0:1]/10)
                op2 = OpDelay(g, 0.00000)
                op2.inputs["Input"].connect(op1.outputs["Data"])
                nucleisrc = LazyflowSource(op2.outputs["Output"])
                op3 = OpDataProvider(g, raw[:,:,:,:,1:2]/5)
                op4 = OpDelay(g, 0.00000)
                op4.inputs["Input"].connect(op3.outputs["Data"])
                membranesrc = LazyflowSource(op4.outputs["Output"])

                layer1 = GrayscaleLayer( membranesrc )
                layer1.name = "Membranes"
                layerstack.append(layer1)
                
                layer2 = RGBALayer( red = nucleisrc )
                layer2.name = "Nuclei"
                layer2.opacity = 0.5
                layerstack.append(layer2)
                
                source = nucleisrc

            elif "manylayers" in argv:
                N = 200
                print "%d Layers!" % N
                fn = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
                raw = np.load(fn)
                print "loading file '%s'" % fn

                op1 = OpDataProvider(g, raw[:,:,:,:,0:1]/10)
                nucleisrc = LazyflowSource(op1.outputs["Data"])
                op2 = OpDataProvider(g, raw[:,:,:,:,1:2]/5)
                membranesrc = LazyflowSource(op2.outputs["Data"])

                layerstack.append(GrayscaleLayer( membranesrc ))

                for i in xrange(N):
                    layer = RGBALayer( red = nucleisrc )
                    layer.opacity = 0.3
                    layerstack.append(layer)
                source = nucleisrc

            elif "label" in argv:
                fn = os.path.split(os.path.abspath(__file__))[0] +"/_testing/5d.npy"
                raw = np.load(fn)

                op1 = OpDataProvider(g, raw[:,:,:,:,0:1]/20)
                op2 = OpDelay(g, 0.00000)
                op2.inputs["Input"].connect(op1.outputs["Data"])
                nucleisrc = LazyflowSource(op2.outputs["Output"])
                op3 = OpDataProvider(g, raw[:,:,:,:,1:2]/10)
                op4 = OpDelay(g, 0.00000)
                op4.inputs["Input"].connect(op3.outputs["Data"])
                membranesrc = LazyflowSource(op4.outputs["Output"])
                
                tint = np.zeros(shape=raw.shape, dtype=np.uint8)
                tint[:] = 255
                tintsrc = ArraySource(tint)

                opLabels = operators.OpSparseLabelArray(g)                                
                opLabels.inputs["shape"].setValue(raw.shape[:-1] + (1,))
                opLabels.inputs["eraser"].setValue(100)                
                opLabels.inputs["Input"][0,0,0,0,0] = 1                    
                opLabels.inputs["Input"][0,0,0,1,0] = 2                    
                
                labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])

                layer1 = RGBALayer( green = membranesrc, red = nucleisrc )
                layer1.name = "Membranes/Nuclei"

                
                layerstack.append(layer1)


                opImage  = operators.OpArrayPiper(g)
                opImage.inputs["Input"].setValue(raw[:,:,:,:,0:1]/20)
                opImage2  = operators.OpArrayPiper(g)
                opImage2.inputs["Input"].setValue(raw[:,:,:,:,1:2]/10)
                
                opImageList = operators.Op5ToMulti(g)    
                opImageList.inputs["Input0"].connect(opImage.outputs["Output"])
                opImageList.inputs["Input1"].connect(opImage2.outputs["Output"])


                opFeatureList = operators.Op5ToMulti(g)    
                opFeatureList.inputs["Input0"].connect(opImageList.outputs["Outputs"])

#                
                stacker=operators.OpMultiArrayStacker(g)
#                
#                opMulti = operators.Op20ToMulti(g)    
#                opMulti.inputs["Input00"].connect(opG.outputs["Output"])
                stacker.inputs["Images"].connect(opFeatureList.outputs["Outputs"])
                stacker.inputs["AxisFlag"].setValue('c')
                stacker.inputs["AxisIndex"].setValue(4)
                
                ################## Training
                opMultiL = operators.Op5ToMulti(g)    
                
                opMultiL.inputs["Input0"].connect(opLabels.outputs["Output"])
                
                opTrain = operators.OpTrainRandomForest(g)
                opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
                opTrain.inputs['Images'].connect(stacker.outputs["Output"])
                opTrain.inputs['fixClassifier'].setValue(False)                

                opClassifierCache = operators.OpArrayCache(g)
                opClassifierCache.inputs["Input"].connect(opTrain.outputs['Classifier'])

                ################## Prediction
                opPredict=operators.OpPredictRandomForest(g)
                opPredict.inputs['LabelsCount'].setValue(2)
                opPredict.inputs['Classifier'].connect(opClassifierCache.outputs['Output'])    
                opPredict.inputs['Image'].connect(stacker.outputs['Output'])            

                
                
                selector=operators.OpSingleChannelSelector(g)
                selector.inputs["Input"].connect(opPredict.outputs['PMaps'])
                selector.inputs["Index"].setValue(1)
                
                opSelCache = operators.OpArrayCache(g)
                opSelCache.inputs["blockShape"].setValue((1,5,5,5,1))
                opSelCache.inputs["Input"].connect(selector.outputs["Output"])                
                
                predictsrc = LazyflowSource(opSelCache.outputs["Output"][0])
                
                layer2 = GrayscaleLayer( predictsrc, normalize = (0.0,1.0) )
                layer2.name = "Prediction"
                layerstack.append( layer2 )

                layer3 = ColortableLayer( labelsrc, colorTable = [QColor(0,0,0,0).rgba(), QColor(255,0,0,255).rgba(), QColor(0,0,255,255).rgba()] )
                layer3.name = "Labels"
                layerstack.append(layer3)                
                source = nucleisrc
            else:
                raise RuntimeError("Invalid testing mode")
        
            arr = None
            if hasattr(source, '_array'):
                arr = source._array
            else:
                arr = source._outslot
            
            shape = None
            if hasattr(source, '_array'):
                shape = source._array.shape
            else:
                shape = source._outslot.shape
            if len(shape) == 3:
                shape = (1,)+shape+(1,)
                
            if "l" in sys.argv:
                from lazyflow import operators
                opLabels = operators.OpSparseLabelArray(g)                                
                opLabels.inputs["shape"].setValue(shape[:-1] + (1,))
                opLabels.inputs["eraser"].setValue(100)                
                opLabels.inputs["Input"][0,0,0,0,0] = 1                    
                opLabels.inputs["Input"][0,0,0,1,0] = 2
                labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])
                layer = ColortableLayer( labelsrc, colorTable = [QColor(0,0,0,0).rgba(), QColor(255,0,0,255).rgba(), QColor(0,0,255,255).rgba()] )
                layer.name = "Labels"
                layerstack.append(layer)

            if "label" in argv or "l" in argv:
                self.editor = VolumeEditor(shape, layerstack, labelsink=labelsrc)
                self.editor.setDrawingEnabled(True)
            else:
                self.editor = VolumeEditor(shape, layerstack)
            self.editor.showDebugPatches = True

            self.widget = VolumeEditorWidget(parent=None, editor=self.editor)
            
            if not 't' in sys.argv:
                #show some initial position
                self.editor.posModel.slicingPos = [5,10,2]
            else:
                def randomMove():
                    self.editor.posModel.slicingPos = [numpy.random.randint(0,shape[i]) for i in range(1,4)]
                t = QTimer(self)
                t.setInterval(3000)
                t.timeout.connect(randomMove)
                t.start()

    app = QApplication(sys.argv)
    
    args = ['hugeslab', 'cuboid', '5d', 'comp', 'layers', 'manylayers', 't', 'label', '3dvol']
    
    if len(sys.argv) < 2 or not any(x in sys.argv for x in args) :
        print "Usage: python volumina.py <testmode> %r" % args 
        app.quit()
        sys.exit(0)
    if len(sys.argv) == 2 and "t" in sys.argv:
        print "the 't' modifier needs to be used together with one of the other options."
        app.quit()
        sys.exit(0)
    
    s = QSplitter()

    t2 = Test(sys.argv)

    s.addWidget(t2.widget)

    fitToViewButton   = QPushButton("fitToView")
    layerWidgetButton = QPushButton("Layers")
    layerWidgetButton.setCheckable(True)

    
    def label1Set():
        t2.editor.brushingModel.setDrawnNumber(1)
    
    def label2Set():
        t2.editor.brushingModel.setDrawnNumber(2)

    label1Button   = QPushButton("Label1")
    label1Button.clicked.connect(label1Set)
    label2Button   = QPushButton("Label2")
    label2Button.clicked.connect(label2Set)

    
    l = QVBoxLayout()
    w = QWidget()
    w.setLayout(l)
    s.addWidget(w)
    
    l.addWidget(fitToViewButton)
    l.addWidget(layerWidgetButton)
    l.addWidget(label1Button)
    l.addWidget(label2Button)  
    
    l.addStretch()

    def fit():
        for i in range(3):
            t2.editor.imageViews[i].changeViewPort(QRectF(0,0,30,30))
    fitToViewButton.toggled.connect(fit)       

    #show rudimentary layer widget
    model = t2.editor.layerStack
    ######################################################################
    view = LayerWidget(None, model)

    w = QWidget()
    lh = QHBoxLayout(w)
    lh.addWidget(view)
    
    up   = QPushButton('Up')
    down = QPushButton('Down')
    delete = QPushButton('Delete')
    add = QPushButton('Add artifical layer')
    lv  = QVBoxLayout()
    lh.addLayout(lv)
    
    lv.addWidget(up)
    lv.addWidget(down)
    lv.addWidget(delete)
    lv.addWidget(add)
    
    w.setGeometry(100, 100, 800,600)
    
    up.clicked.connect(model.moveSelectedUp)
    model.canMoveSelectedUp.connect(up.setEnabled)
    down.clicked.connect(model.moveSelectedDown)
    model.canMoveSelectedDown.connect(down.setEnabled)
    delete.clicked.connect(model.deleteSelected)
    model.canDeleteSelected.connect(delete.setEnabled)

    def addConstantLayer():
        src = ConstantSource(128)
        layer = RGBALayer( green = src )
        layer.name = "Soylent Green"
        layer.opacity = 0.5
        model.append(layer)
    add.clicked.connect(addConstantLayer)
    ######################################################################
    
    def layers(toggled):
        if toggled:
            w.show()
            w.raise_()
        else:
            w.hide()
    layerWidgetButton.toggled.connect(layers)

    s.showMaximized()

    app.exec_()

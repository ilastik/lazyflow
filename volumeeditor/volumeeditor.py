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

from PyQt4.QtCore import Qt, pyqtSignal, QTimer
from PyQt4.QtGui import QApplication, QWidget, QPixmapCache, QLabel, QSpinBox, \
                        QCheckBox, QShortcut, QKeySequence, QSplitter, \
                        QVBoxLayout, QHBoxLayout, QPushButton, QToolButton

import time
import numpy, qimage2ndarray

from ilastikdeps.core.volume import DataAccessor
from ilastikdeps.gui.shortcutmanager import shortcutManager
from ilastikdeps.gui.quadsplitter import QuadView
from ilastikdeps.gui.view3d import OverviewScene
import ilastikdeps.gui.exportDialog as exportDialog
      
from imagescene import ImageScene
from imageSaveThread import ImageSaveThread
from viewManager import ViewManager
from drawManager import DrawManager


from helper import ImageWithProperties, \
HistoryManager, \
InteractionLogger, LabelState, VolumeUpdate, \
is3D, is2D, DummyOverlayListWidget

#*******************************************************************************
# V o l u m e E d i t o r                                                      *
#*******************************************************************************

class VolumeEditor(QWidget):
    changedSlice = pyqtSignal(int,int)
    onOverlaySelected = pyqtSignal(int)
    newLabelsPending = pyqtSignal()
    
    zoomInFactor  = 1.1
    zoomOutFactor = 0.9
    
    @property
    def useOpenGL(self):
        return self.sharedOpenglWidget is not None
    
    def __init__(self, shape, parent, sharedOpenglWidget = None, viewManager = None):
        QWidget.__init__(self, parent)
        
        assert(len(shape) == 5)
        self._shape = shape
            
        self.ilastik = parent   # FIXME: dependency cycle
        self.grid = None #in 3D mode hold the quad view widget, otherwise remains none
        
        # enable interaction logger
        #InteractionLogger()   

        #Bordermargin settings - they control the blue markers that signal the region from wich the
        #labels are not used for trainig
        self.useBorderMargin = False
        self.borderMargin = 0

        #this setting controls the rescaling of the displayed _data to the full 0-255 range
        self.normalizeData = False

        #this settings controls the timer interval during interactive mode
        #set to 0 to wait for complete brushstrokes !
        #self.drawUpdateInterval = 300
        
        self.sharedOpenGLWidget = sharedOpenglWidget


        QPixmapCache.setCacheLimit(100000)

        self.save_thread = ImageSaveThread(self)
        self._history = HistoryManager(self)
        self.drawManager = DrawManager()
        self.viewManager = viewManager

        self.pendingLabels = []


        self.imageScenes = []
        scene0 = ImageScene(0, self.viewManager, self.drawManager, self.sharedOpenGLWidget)
        self.imageScenes.append(scene0)
        
        self.overview = OverviewScene(self, self._shape[1:4])
        
        self.overview.changedSlice.connect(self.changeSlice)
        self.changedSlice.connect(self.overview.ChangeSlice)

        if is3D(self._shape):
            # 3D image          
            scene1 = ImageScene(1, self.viewManager, self.drawManager, self.sharedOpenGLWidget)
            self.imageScenes.append(scene1)
            
            scene2 = ImageScene(2, self.viewManager, self.drawManager, self.sharedOpenGLWidget)
            self.imageScenes.append(scene2)
            
            self.grid = QuadView(self)
            self.grid.addWidget(0, self.imageScenes[2])
            self.grid.addWidget(1, self.imageScenes[0])
            self.grid.addWidget(2, self.imageScenes[1])
            self.grid.addWidget(3, self.overview)
            for i in xrange(3):
                self.imageScenes[i].drawing.connect(self.updateLabels)
                self.imageScenes[i].customContextMenuRequested.connect(self.onCustomContextMenuRequested)
        
        for scene in self.imageScenes:
            scene.mouseDoubleClicked.connect(self.setPosition)
            scene.mouseMoved.connect(self.updateInfoLabels)
            scene.mouseMoved.connect(self.updateCrossHairCursor)
            self.changedSlice.connect(scene.updateSliceIntersection)
            scene.beginDraw.connect(self.beginDraw)
            scene.endDraw.connect(self.endDraw)

            # connect hud slice selectors
            fn = [self.changeSliceX, self.changeSliceY, self.changeSliceZ]
            scene.hud.sliceSelector.valueChanged.connect(fn[scene.axis])
        self.viewManager.sliceChanged.connect(lambda num,axis: self.imageScenes[axis].hud.sliceSelector.setValue(num))            
            
            
            
        #Controls the trade-off of speed and flickering when scrolling through this slice view
        self.setFastRepaint(True)   

        # 2D/3D Views
        viewingLayout = QVBoxLayout()
        viewingLayout.setContentsMargins(10,2,0,2)
        viewingLayout.setSpacing(0)
        if is3D(self._shape):
            viewingLayout.addWidget(self.grid)
            self.grid.setContentsMargins(0,0,10,0)
        else:
            viewingLayout.addWidget(self.imageScenes[0])
        
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
        self.toolBox = QWidget()
        self.toolBoxLayout = QVBoxLayout()
        self.toolBoxLayout.setMargin(5)
        self.toolBox.setLayout(self.toolBoxLayout)
        #self.toolBox.setMaximumWidth(190)
        #self.toolBox.setMinimumWidth(190)

        # Add label widget to toolBoxLayout
        self.labelWidget = None
        #<><><> self.setLabelWidget(DummyLabelWidget())

        self.toolBoxLayout.addStretch()
            
        # Check box for slice intersection marks
        currPosButton = QToolButton()
        currPosButton.setText("Indicate Current Position")
        currPosButton.setCheckable(True)
        currPosButton.setChecked(True)        
        self.toolBoxLayout.addWidget(currPosButton)
        for scene in self.imageScenes:
            currPosButton.toggled.connect(scene.setSliceIntersection)

        # Channel Selector Combo Box in right side toolbox
        self.channelSpin = QSpinBox()
        self.channelSpin.setEnabled(True)
        self.channelSpin.valueChanged.connect(self.setChannel)
        
        self.channelEditBtn = QPushButton('Edit channels')
        self.channelEditBtn.clicked.connect(self.on_editChannels)
        
        channelLayout = QHBoxLayout()
        channelLayout.addWidget(self.channelSpin)
        channelLayout.addWidget(self.channelEditBtn)
        
        self.channelSpinLabel = QLabel("Channel:")
        self.toolBoxLayout.addWidget(self.channelSpinLabel)
        self.toolBoxLayout.addLayout(channelLayout)
        
        #TODO:
        # == 3 checks for RGB image
        if self._shape[-1] == 1 or self._shape[-1] == 3: #only show when needed
            self.channelSpin.setVisible(False)
            self.channelSpinLabel.setVisible(False)
            self.channelEditBtn.setVisible(False)
        self.channelSpin.setRange(0,self._shape[-1] - 1)

        #Overlay selector
        self.overlayWidget = DummyOverlayListWidget(self)
        self.toolBoxLayout.addWidget(self.overlayWidget)


        self.toolBoxLayout.setAlignment( Qt.AlignTop )
        
        # some auxiliary stuff
        self._initShortcuts()
        self.focusAxis =  0
        
        # setup the layout for display
        self.splitter = QSplitter()
        self.splitter.setContentsMargins(0,0,0,0)
        tempWidget = QWidget()
        tempWidget.setLayout(viewingLayout)
        self.splitter.addWidget(tempWidget)
        self.splitter.addWidget(self.toolBox)
        splitterLayout = QVBoxLayout()
        splitterLayout.setMargin(0)
        splitterLayout.setSpacing(0)
        splitterLayout.addWidget(self.splitter)
        self.setLayout(splitterLayout)
        
        self.updateGeometry()
        self.update()
        if self.grid:
            self.grid.update()
        
        #start viewing in the center of the volume
        def initialPosition():
            self.changeSliceX(numpy.floor((self._shape[1] - 1) / 2))
            self.changeSliceY(numpy.floor((self._shape[2] - 1) / 2))
            self.changeSliceZ(numpy.floor((self._shape[3] - 1) / 2))
        QTimer.singleShot(0, initialPosition)
    
    def onCustomContextMenuRequested(self, pos):
        print "Volumeeditor.onCustomContextMenuRequested"
        self.customContextMenuRequested.emit(pos)
              
    def _shortcutHelper(self, keySequence, group, description, parent, function, context = None, enabled = None):
        shortcut = QShortcut(QKeySequence(keySequence), parent, member=function, ambiguousMember=function)
        if context != None:
            shortcut.setContext(context)
        if enabled != None:
            shortcut.setEnabled(True)
        shortcutManager.register(shortcut, group, description)
        return shortcut

    def _initShortcuts(self):
        ##undo/redo and other shortcuts
        self._shortcutHelper("Ctrl+Z", "Labeling", "History undo", self, self.historyUndo, Qt.ApplicationShortcut, True)
        self._shortcutHelper("Ctrl+Shift+Z", "Labeling", "History redo", self, self.historyRedo, Qt.ApplicationShortcut, True)  
        self._shortcutHelper("Ctrl+Y", "Labeling", "History redo", self, self.historyRedo, Qt.ApplicationShortcut, True)
        self._shortcutHelper("Space", "Overlays", "Invert overlay visibility", self, self.toggleOverlays, enabled = True)
        self._shortcutHelper("l", "Labeling", "Go to next label (cyclic, forward)", self, self.nextLabel)
        self._shortcutHelper("k", "Labeling", "Go to previous label (cyclic, backwards)", self, self.prevLabel)
        self._shortcutHelper("x", "Navigation", "Enlarge slice view x to full size", self, self.toggleFullscreenX)
        self._shortcutHelper("y", "Navigation", "Enlarge slice view y to full size", self, self.toggleFullscreenY)
        self._shortcutHelper("z", "Navigation", "Enlarge slice view z to full size", self, self.toggleFullscreenZ)
        self._shortcutHelper("q", "Navigation", "Switch to next channel", self, self.nextChannel)
        self._shortcutHelper("a", "Navigation", "Switch to previous channel", self, self.previousChannel)
        
        for scene in self.imageScenes:
            self._shortcutHelper("n", "Labeling", "Increase brush size", scene, self.drawManager.brushSmaller, Qt.WidgetShortcut)
            self._shortcutHelper("m", "Labeling", "Decrease brush size", scene, self.drawManager.brushBigger, Qt.WidgetShortcut)
        
            self._shortcutHelper("+", "Navigation", "Zoom in", scene, scene.zoomIn, Qt.WidgetShortcut)
            self._shortcutHelper("-", "Navigation", "Zoom out", scene, scene.zoomOut, Qt.WidgetShortcut)
            self._shortcutHelper("p", "Navigation", "Slice up", scene, scene.sliceUp, Qt.WidgetShortcut)           
            self._shortcutHelper("o", "Navigation", "Slice down", scene, scene.sliceDown, Qt.WidgetShortcut)
            self._shortcutHelper("Ctrl+Up", "Navigation", "Slice up", scene, scene.sliceUp, Qt.WidgetShortcut)
            self._shortcutHelper("Ctrl+Down", "Navigation", "Slice down", scene, scene.sliceDown, Qt.WidgetShortcut)
            self._shortcutHelper("Ctrl+Shift+Up", "Navigation", "10 slices up", scene, scene.sliceUp10, Qt.WidgetShortcut)
            self._shortcutHelper("Ctrl+Shift+Down", "Navigation", "10 slices down", scene, scene.sliceDown10, Qt.WidgetShortcut)
        
    def onLabelSelected(self):
        print "xxxxxxxxxxxxxxxxxxxxxx onLabelSelected"
        item = self.labelWidget.currentItem()
        if item is not None:
            for imageScene in self.imageScenes:
                imageScene.drawingEnabled = True
                imageScene.crossHairCursor.setColor(item.color)
        else:
            for imageScene in self.imageScenes:
                imageScene.drawingEnabled = False
                imageScene.crossHairCursor.setColor(QColor("black"))

    def on_editChannels(self):
        from ilastik.gui.channelEditDialog import EditChannelsDialog 
        
        dlg = EditChannelsDialog(self.ilastik.project.dataMgr.selectedChannels, self.ilastik.project.dataMgr[0]._dataVol._data.shape[-1], self)
        
        result = dlg.exec_()
        if result is not None:
            self.ilastik.project.dataMgr.selectedChannels = result

    def on_saveAsImage(self):
        sliceOffsetCheck = False
        if self._shape[1]>1:
            #stack z-view is stored in imageScenes[2], for no apparent reason
            sliceOffsetCheck = True
        timeOffsetCheck = self._shape[0]>1
        formatList = QImageWriter.supportedImageFormats()
        formatList = [x for x in formatList if x in ['png', 'tif']]
        expdlg = exportDialog.ExportDialog(formatList, timeOffsetCheck, sliceOffsetCheck, None, parent=self.ilastik)
        expdlg.exec_()
        try:
            tempname = str(expdlg.path.text()) + "/" + str(expdlg.prefix.text())
            filename = str(QDir.convertSeparators(tempname))
            self.save_thread.start()
            stuff = (filename, expdlg.timeOffset, expdlg.sliceOffset, expdlg.format)
            self.save_thread.queue.append(stuff)
            self.save_thread.imagePending.set()
            
        except:
            pass
        
        
    #Override: QWidget
    def focusNextPrevChild(self, forward = True):
        """this method is overwritten from QWidget
           so that the user can cycle through the three slice views
           using TAB (without giving focus to other widgets in-between)"""
        if forward is True:
            self.focusAxis += 1
            if self.focusAxis > 2:
                self.focusAxis = 0
        else:
            self.focusAxis -= 1
            if self.focusAxis < 0:
                self.focusAxis = 2
                
        if len(self.imageScenes) > 2:
            self.imageScenes[self.focusAxis].setFocus()
        return True
    
    def cleanUp(self):
        QApplication.processEvents()
        print "VolumeEditor: cleaning up "
        for scene in self.imageScenes:
            scene.cleanUp()
            scene.close()
            scene.deleteLater()
        self.imageScenes = []
        self.save_thread.stopped = True
        self.save_thread.imagePending.set()
        self.save_thread.wait()
        QApplication.processEvents()
        print "finished saving thread"

    def setLabelWidget(self,  widget):
        """
        Public interface function for setting the labelWidget toolBox
        """
        if self.labelWidget is not None:
            self.toolBoxLayout.removeWidget(self.labelWidget)
            self.labelWidget.close()
            del self.labelWidget
        self.labelWidget = widget
        self.labelWidget.itemSelectionChanged.connect(self.onLabelSelected)
        self.toolBoxLayout.insertWidget( 0, self.labelWidget)
    
    def setOverlayWidget(self,  widget):
        """
        Public interface function for setting the overlayWidget toolBox
        """
        if self.overlayWidget is not None:
            self.toolBoxLayout.removeWidget(self.overlayWidget)
            self.overlayWidget.close()
            del self.overlayWidget
        self.overlayWidget = widget
        self.overlayWidget.selectedOverlay.connect(self.onOverlaySelected)
        self.toolBoxLayout.insertWidget( 1, self.overlayWidget)        
        self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr.ilastik = self.ilastik

    def setRgbMode(self, mode): 
        """
        change display mode of 3-channel images to either rgb, or 3-channels
        mode can bei either  True or False
        """
        if self._shape[-1] == 3:
            print "setRgbMode: not implemented"
            sys.exit(1)
            #self.image.rgb = mode
            self.channelSpin.setVisible(not mode)
            self.channelSpinLabel.setVisible(not mode)

    def setUseBorderMargin(self, use):
        self.useBorderMargin = use
        self.setBorderMargin(self.borderMargin)

    def setFastRepaint(self, fastRepaint):
        self.fastRepaint = fastRepaint
        for imageScene in self.imageScenes:
            imageScene.fastRepaint = self.fastRepaint

    def setBorderMargin(self, margin):
        if self.useBorderMargin is True:
            if self.borderMargin != margin:
                print "new border margin:", margin
                self.borderMargin = margin
                for imgScene in self.imageScenes:
                    imgScene.setBorderMarginIndicator(margin)
                self.repaint()
        else:
            for imgScene in self.imageScenes:
                imgScene.setBorderMarginIndicator(margin)
                self.repaint()

    def updateTimeSliceForSaving(self, time, num, axis):
        self.imageScenes[axis].thread.freeQueue.clear()
        if self.imageScenes[axis].hud.sliceSelector.value() != num:
            #this will emit the signal and change the slice
            self.imageScenes[axis].hud.sliceSelector.setValue(num)
        elif self.viewManager.time!=time:
            #if only the time is changed, we don't want to update all 3 slices
            self.viewManager.time = time
            self.changeSlice(num, axis)
        else:
            #no need to update, just save the current image
            self.imageScenes[axis].thread.freeQueue.set()
            
    def closeEvent(self, event):
        event.accept()

    def wheelEvent(self, event):
        keys = QApplication.keyboardModifiers()
        k_ctrl = (keys == Qt.ControlModifier)
        
        if k_ctrl is True:        
            if event.delta() > 0:
                scaleFactor = VolumeEditor.zoomInFactor
            else:
                scaleFactor = VolumeEditor.zoomOutFactor
            self.imageScenes[0].doScale(scaleFactor)
            self.imageScenes[1].doScale(scaleFactor)
            self.imageScenes[2].doScale(scaleFactor)
                       
    def repaint(self, axis = None):
        if axis == None:
            axes = range(3)
        else:
            axes = [axis]

        for i in axes:
            tempImage = None
            tempoverlays = []   
            for item in reversed(self.overlayWidget.overlays):
                if item.visible: #and hasattr(item, 'getOverlaySlice'):
                    tempoverlays.append(item.getOverlaySlice(self.viewManager.slicePosition[i], i, self.viewManager.time, item.channel))
            if len(self.overlayWidget.overlays) > 0 and self.overlayWidget.getOverlayRef("Raw Data") is not None:
                tempImage = self.overlayWidget.getOverlayRef("Raw Data")._data.getSlice(self.viewManager.slicePosition[i], i, self.viewManager.time, self.overlayWidget.getOverlayRef("Raw Data").channel)
            else:
                tempImage = None

            if len(self.imageScenes) > i:
                self.imageScenes[i].displayNewSlice(tempImage, tempoverlays, fastPreview = False, normalizeData = self.normalizeData)
                        
    def show(self):
        QWidget.show(self)

    def setLabels(self, offsets, axis, num, labels, erase):
        """
        offsets: labels is a 2D matrix in the image plane perpendicular to axis, which is offset from the origin
                 of the slice by the 2D offsets vector
        axis:    the axis (x=0, y=1 or z=2 which is perpendicular to the image plane
        num:     position of the image plane perpendicular to axis on which the 'labels' were drawn (the slice number)
        labels   2D matrix of new labels
        erase    boolean whether we are erasing or not. This changes how we interprete the update defined through
                 'labels'
        """
        
        if axis == 0:
            offsets5 = (self.viewManager.time,num,offsets[0],offsets[1],0)
            sizes5 = (1,1,labels.shape[0], labels.shape[1],1)
        elif axis == 1:
            offsets5 = (self.viewManager.time,offsets[0],num,offsets[1],0)
            sizes5 = (1,labels.shape[0],1, labels.shape[1],1)
        else:
            offsets5 = (self.viewManager.time,offsets[0],offsets[1],num,0)
            sizes5 = (1,labels.shape[0], labels.shape[1],1,1)
        
        vu = VolumeUpdate(labels.reshape(sizes5),offsets5, sizes5, erase)
        vu.applyTo(self.labelWidget.overlayItem)
        self.pendingLabels.append(vu)

        patches = self.imageScenes[axis].patchAccessor.getPatchesForRect(offsets[0], offsets[1],offsets[0]+labels.shape[0], offsets[1]+labels.shape[1])

        tempImage = None
        tempoverlays = []
        for item in reversed(self.overlayWidget.overlays):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(self.viewManager.slicePosition[axis],axis, self.viewManager.time, 0))

        if len(self.overlayWidget.overlays) > 0:
            tempImage = self.overlayWidget.getOverlayRef("Raw Data")._data.getSlice(num, axis, self.viewManager.time, self.viewManager.channel)
        else:
            tempImage = None            

        # FIXME there needs to be abstraction
        self.imageScenes[axis].imageSceneRenderer.updatePatches(patches, tempImage, tempoverlays)
        self.newLabelsPending.emit() # e.g. retrain

    #===========================================================================
    # View & Tools Options
    #===========================================================================
    def toggleOverlays(self):
        for index,  item in enumerate(self.overlayWidget.overlays):
            item.visible = not(item.visible)
            checkState = Qt.Checked if item.visible else Qt.Unchecked
            self.overlayWidget.overlayListWidget.item(index).setCheckState(checkState)
        self.repaint()
       
    def nextChannel(self):
        self.channelSpin.setValue(self.viewManager.channel + 1)

    def previousChannel(self):
        self.channelSpin.setValue(self.viewManager.channel - 1)
        
    def toggleFullscreenX(self):
        self.maximizeSliceView(0)

    def toggleFullscreenY(self):
        self.maximizeSliceView(1)

    def toggleFullscreenZ(self):
        self.maximizeSliceView(2)

    def maximizeSliceView(self, axis):
        if axis == 2:
            self.grid.toggleMaximized(0)
        if axis == 1:
            self.grid.toggleMaximized(2)
        if axis == 0:
            self.grid.toggleMaximized(1)
          
    def nextLabel(self):
        self.labelWidget.nextLabel()
        
    def prevLabel(self):
        self.labelWidget.nextLabel()
        
    def historyUndo(self):
        self._history.undo()

    def historyRedo(self):
        self._history.redo()

    #===========================================================================
    # Navigation in Volume
    #===========================================================================        
    def setChannel(self, channel):
        if len(self.overlayWidget.overlays) > 0:
            ov = self.overlayWidget.getOverlayRef("Raw Data")
            if ov.shape[-1] == self._shape[-1]:
                self.overlayWidget.getOverlayRef("Raw Data").channel = channel
            
        self.viewManager.setChannel(time)
        #FIXME remove
        for i in range(3):
            self.changeSlice(self.viewManager.slicePosition[i], i)

    def setTime(self, time):
        self.viewManager.setTime(time)
        #FIXME remove
        for i in range(3):
            self.changeSlice(self.viewManager.slicePosition[i], i)
            
    def setPosition(self, axis, x, y):
        print "setPosition(%d, %d, %d)" % (axis, x, y)
        if axis == 0:
            self.changeSlice(x, 1)
            self.changeSlice(y, 2)
        elif axis == 1:
            self.changeSlice(x, 0)
            self.changeSlice(y, 2)
        elif axis ==2:
            self.changeSlice(x, 0)
            self.changeSlice(y, 1)
            
    def changeSliceX(self, num):
        self.changeSlice(num, 0)

    def changeSliceY(self, num):
        self.changeSlice(num, 1)

    def changeSliceZ(self, num):
        self.changeSlice(num, 2)
        
    def changeSlice(self, num, axis):
        self.viewManager.setSlice(num, axis)
        
        if len(self.imageScenes) > axis:
            self.imageScenes[axis].sliceNumber = num
        
        #print "VolumeEditor.changeSlice: emitting 'changedSlice' signal num=%d, axis=%d" % (num,axis)
        self.changedSlice.emit(num, axis) # FIXME this triggers the update for live prediction 
        
        self.repaint(axis)
        
        
    def getVisibleState(self):
        return self.viewManager.getVisibleState()


    # from imagescene
    
    def beginDraw(self, axis, pos):
        print "VolumeEditor.beginDraw FIXME self.labelWidget.ensureLabelOverlayVisible()"
        
    def endDraw(self, axis, pos):
        result = self.drawManager.endDrawing(pos)
        print "endDraw: result =", result
        self.updateLabels(axis, pos)
        #FIXME
        #self.pushLabelsToLabelWidget()

    def pushLabelsToLabelWidget(self):
        newLabels = self.getPendingLabels()
        self.labelWidget.labelMgr.newLabels(newLabels)
        
    def updateLabels(self, axis, mousePos):
        result = self.drawManager.dumpDraw(mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.drawManager.drawnNumber
        labels = numpy.where(labels > 0, number, 0)
        ls = LabelState('drawing', axis, self.viewManager.slicePosition[axis], result[0:2], labels.shape, self.viewManager.time, self, self.drawManager.erasing, labels, number)
        self._history.append(ls)        
        self.setLabels(result[0:2], axis, self.viewManager.slicePosition[axis], labels, self.drawManager.erasing)
        
    def getPendingLabels(self):
        temp = self.pendingLabels
        self.pendingLabels = []
        return temp
    
    def updateCrossHairCursor(self, axis, x, y, valid):
        if valid:
            self.imageScenes[axis].crossHairCursor.showXYPosition(x,y)
            
            if axis == 0: # x-axis
                if len(self.imageScenes) > 2:
                    yView = self.imageScenes[1].crossHairCursor
                    zView = self.imageScenes[2].crossHairCursor
                    
                    yView.setVisible(False)
                    zView.showYPosition(x, y)
            elif axis == 1: # y-axis
                xView = self.imageScenes[0].crossHairCursor
                zView = self.imageScenes[2].crossHairCursor
                
                zView.showXPosition(x, y)
                xView.setVisible(False)
            else: # z-axis
                xView = self.imageScenes[0].crossHairCursor
                yView = self.imageScenes[1].crossHairCursor
                    
                xView.showXPosition(y, x)
                yView.showXPosition(x, y)
    
    def updateInfoLabels(self, axis, x, y, valid):
        if not valid:
            return
        
        (posX, posY, posZ) = self.imageScenes[axis].coordinateUnderCursor()

        #if hasattr(self.overlayWidget, 'getOverlayRef'):
        if axis == 0:
            colorValues = self.overlayWidget.getOverlayRef("Raw Data").getOverlaySlice(posX, 0, time=0, channel=0)._data[x,y]
        elif axis == 1:
            colorValues = self.overlayWidget.getOverlayRef("Raw Data").getOverlaySlice(posY, 1, time=0, channel=0)._data[x,y]
        else:
            colorValues = self.overlayWidget.getOverlayRef("Raw Data").getOverlaySlice(posZ, 2, time=0, channel=0)._data[x,y]

        self.posLabel.setText("<b>x:</b> %03i  <b>y:</b> %03i  <b>z:</b> %03i" % (posX, posY, posZ))
        if isinstance(colorValues, numpy.ndarray):
            self.pixelValuesLabel.setText("<b>R:</b> %03i  <b>G:</b> %03i  <b>B:</b> %03i" % (colorValues[0], colorValues[1], colorValues[2]))
        else:
            self.pixelValuesLabel.setText("<b>Gray:</b> %03i" %int(colorValues))

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    import sys
    from PyQt4.QtCore import QObject, QTimer
    from PyQt4.QtGui import QApplication, QColor, QSplitter
    from PyQt4.QtOpenGL import QGLWidget
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from ilastikdeps.core.overlayMgr import OverlaySlice, OverlayItem
    from ilastikdeps.core.volume import DataAccessor
    
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

        center = numpy.asarray((N2,N2,N2))
        s[(X-10)**2+(Y-10)**2+(Z-15)**2 < (N2-2)**2] = 0

        s[(X-30)**2+(Y-30)**2+(Z-30)**2 < (10)**2] = 128

        s[0:10,0:10,0:10] = 200
        
        return s
    
    class Test(QObject):
        def __init__(self, useGL, testmode):
            QObject.__init__(self)
            
            if testmode == "hugeslab":
                N = 2000
                self.data = (numpy.random.rand(N,2*N, 10)*255).astype(numpy.uint8)
            elif testmode == "cuboid":
                N = 100
                from testing import testVolume
                self.data = testVolume(N)
            else:
                raise RuntimeError("Invalid testing mode")
            
            sharedOpenglWidget = None
            if useGL:
                sharedOpenglWidget=QGLWidget()
            
            vm = ViewManager(self.data)
            self.dialog = VolumeEditor((1,)+self.data.shape+(1,), None, sharedOpenglWidget=sharedOpenglWidget, viewManager=vm)
            for i in range(3):
                self.dialog.imageScenes[i].drawingEnabled = True
            
            self.dataOverlay = OverlayItem(DataAccessor(self.data), alpha=1.0, color=Qt.black, colorTable=OverlayItem.createDefaultColorTable('GRAY', 256), autoVisible=True, autoAlphaChannel=False)
            self.dialog.overlayWidget.overlays = [self.dataOverlay.getRef()]
            
            self.dialog.show()
            self.dialog.setPosition(0,0,0)
            self.dialog.setPosition(1,0,0)
            self.dialog.setPosition(2,0,0)

    app = QApplication(sys.argv)
    
    if len(sys.argv) < 2:
        raise RuntimeError("Usage: python volumeeditor.py <testmode> (hugeslab or cuboid)")
    testmode = sys.argv[1]
    
    s = QSplitter()
    t1 = Test(True, testmode)
    t2 = Test(False, testmode)
    s.addWidget(t1.dialog)
    s.addWidget(t2.dialog)
    
    s.show()
    
    app.exec_()


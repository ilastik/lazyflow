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

from PyQt4.QtCore import Qt, pyqtSignal, QDir
from PyQt4.QtGui import QApplication, QWidget, QLabel, QSpinBox, \
                        QShortcut, QKeySequence, QSplitter, \
                        QVBoxLayout, QHBoxLayout, QPushButton, QToolButton, QImageWriter

import numpy, qimage2ndarray

from quadsplitter import QuadView
from view3d.view3d import OverviewScene
from exportDialog import ExportDialog
      
from imageView2D import ImageView2D
from imageSaveThread import ImageSaveThread
from navigationControler import NavigationControler
from drawManager import DrawManager
from sliceSelectorHud import SliceSelectorHud

from helper import HistoryManager, LabelState, VolumeUpdate, is3D
from PyQt4 import QtCore

#*******************************************************************************
# V o l u m e E d i t o r                                                      *
#*******************************************************************************

class VolumeEditor(QWidget):
    changedSlice      = pyqtSignal(int,int)
    onOverlaySelected = pyqtSignal(int)
    newLabelsPending  = pyqtSignal()
    
    zoomInFactor  = 1.1
    zoomOutFactor = 0.9
    
    def __init__(self, shape, parent, useGL = False, viewManager = None):
        QWidget.__init__(self, parent)
        
        assert(len(shape) == 5)
        self._shape = shape
            
        self.ilastik = parent   # FIXME: dependency cycle
        self._grid = None #in 3D mode hold the quad view widget, otherwise remains none
        
        # enable interaction logger
        #InteractionLogger()   

        #Bordermargin settings - they control the blue markers that signal the region from which the
        #labels are not used for trainig
        self._useBorderMargin = False
        self._borderMargin = 0

        #this setting controls the rescaling of the displayed _data to the full 0-255 range
        self.normalizeData = False

        #this settings controls the timer interval during interactive mode
        #set to 0 to wait for complete brushstrokes !
        #self.drawUpdateInterval = 300

        self._saveThread = ImageSaveThread(self)
        self._history = HistoryManager(self)
        self._drawManager = DrawManager()
        self._viewManager = viewManager

        self._pendingLabels = []

        self._imageViews = []
        scene0 = ImageView2D(self._drawManager, useGL=useGL)
        self._imageViews.append(scene0)
        
        self._overview = OverviewScene(self, self._shape[1:4])

        #FIXME: resurrect        
        #self._overview.changedSlice.connect(self.changeSlice)
        self.changedSlice.connect(self._overview.ChangeSlice)

        if is3D(self._shape):
            # 3D image          
            scene1 = ImageView2D(self._drawManager, useGL=useGL)
            self._imageViews.append(scene1)
            
            scene2 = ImageView2D(self._drawManager, useGL=useGL)
            self._imageViews.append(scene2)
            
            self._grid = QuadView(self)
            self._grid.addWidget(0, self._imageViews[2])
            self._grid.addWidget(1, self._imageViews[0])
            self._grid.addWidget(2, self._imageViews[1])
            self._grid.addWidget(3, self._overview)
            for i in xrange(3):
                self._imageViews[i].drawing.connect(self.updateLabels)
                self._imageViews[i].customContextMenuRequested.connect(self.onCustomContextMenuRequested)
        
        for v in self._imageViews:
            v.beginDraw.connect(self.beginDraw)
            v.endDraw.connect(self.endDraw)
            v.hud = SliceSelectorHud()

        #Controls the trade-off of speed and flickering when scrolling through this slice view
        self.setFastRepaint(True)   

        # 2D/3D Views
        viewingLayout = QVBoxLayout()
        viewingLayout.setContentsMargins(10,2,0,2)
        viewingLayout.setSpacing(0)
        if is3D(self._shape):
            viewingLayout.addWidget(self._grid)
            self._grid.setContentsMargins(0,0,10,0)
        else:
            viewingLayout.addWidget(self._imageViews[0])
        
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
        
        # Add label widget to toolBoxLayout
        self.labelWidget = None

        self._toolBoxLayout.addStretch()
            
        # Check box for slice intersection marks
        self.indicateSliceIntersectionButton = QToolButton()
        self.indicateSliceIntersectionButton.setText("Indicate Current Position")
        self.indicateSliceIntersectionButton.setCheckable(True)
        self.indicateSliceIntersectionButton.setChecked(True)        
        self._toolBoxLayout.addWidget(self.indicateSliceIntersectionButton)

        #Channel Selector QComboBox in right side tool box
        self._channelSpin = QSpinBox()
        self._channelSpin.setEnabled(True)
        
        self.channelEditBtn = QPushButton('Edit channels')
        self.channelEditBtn.clicked.connect(self.on_editChannels)
        
        channelLayout = QHBoxLayout()
        channelLayout.addWidget(self._channelSpin)
        channelLayout.addWidget(self.channelEditBtn)
        
        self._channelSpinLabel = QLabel("Channel:")
        self._toolBoxLayout.addWidget(self._channelSpinLabel)
        self._toolBoxLayout.addLayout(channelLayout)
        
        #TODO:
        # == 3 checks for RGB image
        if self._shape[-1] == 1 or self._shape[-1] == 3: #only show when needed
            self._channelSpin.setVisible(False)
            self._channelSpinLabel.setVisible(False)
            self.channelEditBtn.setVisible(False)
        self._channelSpin.setRange(0,self._shape[-1] - 1)

        #Overlay selector
        self.overlayWidget = None

        self._toolBoxLayout.setAlignment(Qt.AlignTop)
        
        # some auxiliary stuff
        self._initShortcuts()
        
        self.focusAxis =  0 #the currently focused axis
        
        #setup the layout for display
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
        
        self.updateGeometry()
        self.update()
        if self._grid:
            self._grid.update()
        
    def setDrawingEnabled(self, enabled): 
        for i in range(3):
            self._imageViews[i].drawingEnabled = enabled
    
    def onCustomContextMenuRequested(self, pos):
        print "Volumeeditor.onCustomContextMenuRequested"
        self.customContextMenuRequested.emit(pos)

    #===========================================================================
    # Shortcuts
    #===========================================================================              
    def _shortcutHelper(self, keySequence, group, description, parent, function, context = None, enabled = None):
        shortcut = QShortcut(QKeySequence(keySequence), parent, member=function, ambiguousMember=function)
        if context != None:
            shortcut.setContext(context)
        if enabled != None:
            shortcut.setEnabled(True)
        return shortcut, group, description

    def _initShortcuts(self):
        self.shortcuts = []
        self.shortcuts.append(self._shortcutHelper("Ctrl+Z", "Labeling", "History undo", self, self.historyUndo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Z", "Labeling", "History redo", self, self.historyRedo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Ctrl+Y", "Labeling", "History redo", self, self.historyRedo, Qt.ApplicationShortcut, True))
        self.shortcuts.append(self._shortcutHelper("Space", "Overlays", "Invert overlay visibility", self, self.toggleOverlays, enabled = True))
        self.shortcuts.append(self._shortcutHelper("l", "Labeling", "Go to next label (cyclic, forward)", self, self.nextLabel))
        self.shortcuts.append(self._shortcutHelper("k", "Labeling", "Go to previous label (cyclic, backwards)", self, self.prevLabel))
        self.shortcuts.append(self._shortcutHelper("x", "Navigation", "Enlarge slice view x to full size", self, self.toggleFullscreenX))
        self.shortcuts.append(self._shortcutHelper("y", "Navigation", "Enlarge slice view y to full size", self, self.toggleFullscreenY))
        self.shortcuts.append(self._shortcutHelper("z", "Navigation", "Enlarge slice view z to full size", self, self.toggleFullscreenZ))
        self.shortcuts.append(self._shortcutHelper("q", "Navigation", "Switch to next channel", self, self.nextChannel))
        self.shortcuts.append(self._shortcutHelper("a", "Navigation", "Switch to previous channel", self, self.previousChannel))
        
        for scene in self._imageViews:
            self.shortcuts.append(self._shortcutHelper("n", "Labeling", "Increase brush size", scene, self._drawManager.brushSmaller, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("m", "Labeling", "Decrease brush size", scene, self._drawManager.brushBigger, Qt.WidgetShortcut))
        
            self.shortcuts.append(self._shortcutHelper("+", "Navigation", "Zoom in", scene, scene.zoomIn, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("-", "Navigation", "Zoom out", scene, scene.zoomOut, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("p", "Navigation", "Slice up", scene, scene.sliceUp, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("o", "Navigation", "Slice down", scene, scene.sliceDown, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Up", "Navigation", "Slice up", scene, scene.sliceUp, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Down", "Navigation", "Slice down", scene, scene.sliceDown, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Up", "Navigation", "10 slices up", scene, scene.sliceUp10, Qt.WidgetShortcut))
            self.shortcuts.append(self._shortcutHelper("Ctrl+Shift+Down", "Navigation", "10 slices down", scene, scene.sliceDown10, Qt.WidgetShortcut))
        
    def onLabelSelected(self):
        item = self.labelWidget.currentItem()
        if item is not None:
            for imageScene in self._imageViews:
                imageScene.drawingEnabled = True
                imageScene.crossHairCursor.setColor(item.color)
        else:
            for imageScene in self._imageViews:
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
        expdlg = ExportDialog(formatList, timeOffsetCheck, sliceOffsetCheck, None, parent=self.ilastik)
        expdlg.exec_()
        try:
            tempname = str(expdlg.path.text()) + "/" + str(expdlg.prefix.text())
            filename = str(QDir.convertSeparators(tempname))
            self._saveThread.start()
            stuff = (filename, expdlg.timeOffset, expdlg.sliceOffset, expdlg.format)
            self._saveThread.queue.append(stuff)
            self._saveThread.imagePending.set()
            
        except:
            pass
    
    def focusNextPrevChild(self, forward = True):
        """this method is overwritten from QWidget
           so that the user can cycle through the three slice views
           using TAB (without giving focus to other widgets in-between)"""
        if forward:
            self.focusAxis += 1
            if self.focusAxis > 2:
                self.focusAxis = 0
        else:
            self.focusAxis -= 1
            if self.focusAxis < 0:
                self.focusAxis = 2
                
        if len(self._imageViews) > 2:
            self._imageViews[self.focusAxis].setFocus()
        return True
    
    def cleanUp(self):
        QApplication.processEvents()
        print "VolumeEditor: cleaning up "
        for scene in self._imageViews:
            scene.cleanUp()
            scene.close()
            scene.deleteLater()
        self._imageViews = []
        self._saveThread.stopped = True
        self._saveThread.imagePending.set()
        self._saveThread.wait()
        QApplication.processEvents()
        print "finished saving thread"

    def setLabelWidget(self,  widget):
        """
        Public interface function for setting the labelWidget toolBox
        """
        if self.labelWidget is not None:
            self._toolBoxLayout.removeWidget(self.labelWidget)
            self.labelWidget.close()
            del self.labelWidget
        self.labelWidget = widget
        self.labelWidget.itemSelectionChanged.connect(self.onLabelSelected)
        self._toolBoxLayout.insertWidget(0, self.labelWidget)
    
    def setOverlayWidget(self,  widget):
        """
        Public interface function for setting the overlayWidget toolBox
        """
        if self.overlayWidget:
            self._toolBoxLayout.removeWidget(self.overlayWidget)
            self.overlayWidget.close()
            del self.overlayWidget
        self.overlayWidget = widget
        self.overlayWidget.selectedOverlay.connect(self.onOverlaySelected)
        self._toolBoxLayout.insertWidget( 1, self.overlayWidget)
        
        #FIXME: porting
        if self.ilastik:        
            self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr.ilastik = self.ilastik

        #FIXME: porting
        for view in self._imageViews:
            view.porting_overlaywidget = self.overlayWidget

    def setRgbMode(self, mode): 
        """
        change display mode of 3-channel images to either rgb, or 3-channels
        mode can bei either  True or False
        """
        if self._shape[-1] == 3:
            #FIXME
            #self.image does not exist anymore,
            #so this is not possible
            #self.image.rgb = mode
            self._channelSpin.setVisible(not mode)
            self._channelSpinLabel.setVisible(not mode)

    def setUseBorderMargin(self, use):
        self._useBorderMargin = use
        self.setBorderMargin(self._borderMargin)

    def setFastRepaint(self, fastRepaint):
        self.fastRepaint = fastRepaint
        for imageScene in self._imageViews:
            imageScene.fastRepaint = self.fastRepaint

    def setBorderMargin(self, margin):
        if self._useBorderMargin:
            if self._borderMargin != margin:
                print "new border margin:", margin
                self._borderMargin = margin
                for imgScene in self._imageViews:
                    imgScene.setBorderMarginIndicator(margin)
                self.repaint()
        else:
            for imgScene in self._imageViews:
                #FIXME this looks wrong
                imgScene.setBorderMarginIndicator(margin)
                self.repaint()

    def updateTimeSliceForSaving(self, time, num, axis):
        self._imageViews[axis].thread.freeQueue.clear()
        if self._imageViews[axis].hud.sliceSelector.value() != num:
            #this will emit the signal and change the slice
            self._imageViews[axis].hud.sliceSelector.setValue(num)
        elif self._viewManager.time!=time:
            #if only the time is changed, we don't want to update all 3 slices
            self._viewManager.time = time
            self.changeSlice(num, axis)
        else:
            #no need to update, just save the current image
            self._imageViews[axis].thread.freeQueue.set()
            
    def closeEvent(self, event):
        event.accept()

    def wheelEvent(self, event):
        #Implementing the wheel event for the whole 'volumeeditor' widget
        #enables zooming all three slice views at once using the
        #Ctrl+<mouse wheel> shortcut
        keys = QApplication.keyboardModifiers()
        k_ctrl = (keys == Qt.ControlModifier)
        
        if k_ctrl:        
            if event.delta() > 0:
                scaleFactor = VolumeEditor.zoomInFactor
            else:
                scaleFactor = VolumeEditor.zoomOutFactor
            self._imageViews[0].doScale(scaleFactor)
            self._imageViews[1].doScale(scaleFactor)
            self._imageViews[2].doScale(scaleFactor)

    def setLabels(self, offsets, axis, num, labels, erase):
        """
        offsets: labels is a 2D matrix in the image plane perpendicular to axis, which is offset from the origin
                 of the slice by the 2D offsets vector
        axis:    the axis (x=0, y=1 or z=2) which is perpendicular to the image plane
        num:     position of the image plane perpendicular to axis on which the 'labels' were drawn (the slice number)
        labels   2D matrix of new labels
        erase    boolean whether we are erasing or not. This changes how we interpret the update defined through
                 'labels'
        """
        
        if axis == 0:
            offsets5 = (self._viewManager.time,num,offsets[0],offsets[1],0)
            sizes5 = (1,1,labels.shape[0], labels.shape[1],1)
        elif axis == 1:
            offsets5 = (self._viewManager.time,offsets[0],num,offsets[1],0)
            sizes5 = (1,labels.shape[0],1, labels.shape[1],1)
        else:
            offsets5 = (self._viewManager.time,offsets[0],offsets[1],num,0)
            sizes5 = (1,labels.shape[0], labels.shape[1],1,1)
        
        vu = VolumeUpdate(labels.reshape(sizes5),offsets5, sizes5, erase)
        vu.applyTo(self.labelWidget.overlayItem)
        self._pendingLabels.append(vu)

        patches = self._imageViews[axis].patchAccessor.getPatchesForRect(offsets[0], offsets[1],offsets[0]+labels.shape[0], offsets[1]+labels.shape[1])

        tempImage = None
        tempoverlays = []
        for item in reversed(self.overlayWidget.overlays):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(self._viewManager.slicePosition[axis],axis, self._viewManager.time, 0))

        if len(self.overlayWidget.overlays) > 0:
            tempImage = self.overlayWidget.getOverlayRef("Raw Data")._data.getSlice(num, axis, self._viewManager.time, self._viewManager.channel)       

        # FIXME there needs to be abstraction
        self._imageViews[axis].imageSceneRenderer.updatePatches(patches, tempImage, tempoverlays)
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
        self._channelSpin.setValue(self._viewManager.channel + 1)

    def previousChannel(self):
        self._channelSpin.setValue(self._viewManager.channel - 1)
        
    def toggleFullscreenX(self):
        self.maximizeSliceView(0)

    def toggleFullscreenY(self):
        self.maximizeSliceView(1)

    def toggleFullscreenZ(self):
        self.maximizeSliceView(2)

    def maximizeSliceView(self, axis):
        if axis == 2:
            self._grid.toggleMaximized(0)
        if axis == 1:
            self._grid.toggleMaximized(2)
        if axis == 0:
            self._grid.toggleMaximized(1)
          
    def nextLabel(self):
        self.labelWidget.nextLabel()
        
    def prevLabel(self):
        self.labelWidget.nextLabel()
        
    def historyUndo(self):
        self._history.undo()

    def historyRedo(self):
        self._history.redo()

    def getVisibleState(self):
        return self._viewManager.getVisibleState()

    def beginDraw(self, axis, pos):
        print "VolumeEditor.beginDraw FIXME self.labelWidget.ensureLabelOverlayVisible()"
        
    def endDraw(self, axis, pos):
        result = self._drawManager.endDrawing(pos)
        print "endDraw: result =", result
        self.updateLabels(axis, pos)
        #FIXME
        #self.pushLabelsToLabelWidget()

    def pushLabelsToLabelWidget(self):
        #FIXME
        newLabels = self.getPendingLabels()
        self.labelWidget.labelMgr.newLabels(newLabels)
        
    def updateLabels(self, axis, mousePos):
        result = self._drawManager.dumpDraw(mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self._drawManager.drawnNumber
        labels = numpy.where(labels > 0, number, 0)
        ls = LabelState('drawing', axis, self._viewManager.slicePosition[axis], result[0:2], labels.shape, self._viewManager.time, self, self._drawManager.erasing, labels, number)
        self._history.append(ls)        
        self.setLabels(result[0:2], axis, self._viewManager.slicePosition[axis], labels, self._drawManager.erasing)
        
    def getPendingLabels(self):
        temp = self._pendingLabels
        self._pendingLabels = []
        return temp
    
    def updateInfoLabels(self, axis, x, y, valid):
        if not valid:
            return       
#FIXME: resurrect
#        pos = (posX, posY, posZ) = self._imageViews[axis].coordinateUnderCursor()
#        colorValues = self.overlayWidget.getOverlayRef("Raw Data").getOverlaySlice(pos[axis], axis, time=0, channel=0)._data[x,y]
#        
#        self.posLabel.setText("<b>x:</b> %03i  <b>y:</b> %03i  <b>z:</b> %03i" % (posX, posY, posZ))
#        
#        #FIXME RGB is a special case only
#        if isinstance(colorValues, numpy.ndarray):
#            self.pixelValuesLabel.setText("<b>R:</b> %03i  <b>G:</b> %03i  <b>B:</b> %03i" % (colorValues[0], colorValues[1], colorValues[2]))
#        else:
#            self.pixelValuesLabel.setText("<b>Gray:</b> %03i" %int(colorValues))

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    import sys
    from PyQt4.QtCore import QObject, QRectF
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
            
            self.dialog = VolumeEditor((1,)+self.data.shape+(1,), None, useGL=useGL)
            nc = NavigationControler(self.dialog._imageViews, self.data)
            self.dialog.setDrawingEnabled(True)
            
            #FIXME: port to ilastik
            self.dialog.indicateSliceIntersectionButton.toggled.connect(nc.onIndicateSliceIntersectionToggle)
            self.dialog._channelSpin.valueChanged.connect(nc.onChannelChange)
            
            self.dataOverlay = OverlayItem(DataAccessor(self.data), alpha=1.0, color=Qt.black, colorTable=OverlayItem.createDefaultColorTable('GRAY', 256), autoVisible=True, autoAlphaChannel=False)
            
            class FakeOverlayWidget(QWidget):
                selectedOverlay = pyqtSignal(int)
                def __init__(self):
                    QWidget.__init__(self)
                    self.overlays = None
                def getOverlayRef(self, key):
                    return self.overlays[0]
            
            overlayWidget = FakeOverlayWidget()
            overlayWidget.overlays = [self.dataOverlay.getRef()]
            
            self.dialog.setOverlayWidget(overlayWidget)
            
            self.dialog.show()
            
            #show some initial position
            nc.slicingPos = [5,10,2]
            
            self.dialog.setOverlayWidget(overlayWidget)

    app = QApplication(sys.argv)
    
    if len(sys.argv) < 2:
        raise RuntimeError("Usage: python volumeeditor.py <testmode> (hugeslab or cuboid)")
    testmode = sys.argv[1]
    
    s = QSplitter()
    t1 = Test(True, testmode)
    t2 = Test(False, testmode)
    s.addWidget(t1.dialog)
    s.addWidget(t2.dialog)
    
    button=QPushButton("fitToView");
    
    s.addWidget(button)
    
    def fit():
        for i in range(3):
            t1.dialog._imageViews[i].changeViewPort(QRectF(80,20,30,60))
            t2.dialog._imageViews[i].changeViewPort(QRectF(0,0,30,30))
            
    button.clicked.connect(fit)       
    
    s.showMaximized()

    app.exec_()


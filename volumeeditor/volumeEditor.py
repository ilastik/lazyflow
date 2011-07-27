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

from PyQt4.QtCore import Qt, pyqtSignal, QDir, QObject
from PyQt4.QtGui import QApplication, QImageWriter

import numpy, qimage2ndarray
from functools import partial

from imageSaveThread import ImageSaveThread
from historyManager import HistoryManager
from drawManager import DrawManager
from imageScene2D import ImageScene2D
from imageView2D import ImageView2D
from positionModel import PositionModel
from navigationControler import NavigationControler, NavigationInterpreter
from pixelpipeline.slicesources import SpatialSliceSource
from pixelpipeline.imagesources import GrayscaleImageSource
from imagesourcefactories import createImageSource

class VolumeEditor( QObject ):
    changedSlice      = pyqtSignal(int,int)
    onOverlaySelected = pyqtSignal(int)
    newLabelsPending  = pyqtSignal()
    
    zoomInFactor  = 1.1
    zoomOutFactor = 0.9

    def __init__( self, shape, layers, useGL = False):
        super(VolumeEditor, self).__init__()
        assert(len(shape) == 5)
        self._shape = shape

        #this setting controls the rescaling of the displayed _data to the full 0-255 range
        self.normalizeData = False

        #this settings controls the timer interval during interactive mode
        #set to 0 to wait for complete brushstrokes !
        #self.drawUpdateInterval = 300

        self._saveThread = ImageSaveThread(self)
        self._history = HistoryManager(self)
        self._drawManager = DrawManager()

        self._pendingLabels = []

        # three ortho slices
        self.sliceSources = [[], [], []]
        array2dsrcs = []

        for layeridx in xrange(len(layers)):
            array2dsrcs.append([])
            for datasrc in layers[layeridx].datasources:
                array2dsrcs[-1].append([])
                array2dsrcs[-1].append([])
                array2dsrcs[-1].append([])

                if datasrc != None:
                    self.sliceSources[0].append(SpatialSliceSource(datasrc, 'x'))
                    self.sliceSources[1].append(SpatialSliceSource(datasrc, 'y'))
                    self.sliceSources[2].append(SpatialSliceSource(datasrc, 'z'))
                    array2dsrcs[layeridx][0].append(self.sliceSources[0][-1])
                    array2dsrcs[layeridx][1].append(self.sliceSources[1][-1])
                    array2dsrcs[layeridx][2].append(self.sliceSources[2][-1])
                else:
                    array2dsrcs[layeridx][0].append(None)
                    array2dsrcs[layeridx][1].append(None)
                    array2dsrcs[layeridx][2].append(None)

        # ortho image sources
        imageSources = [[], [], []]
        for axis in xrange(3):
            for layeridx in xrange(len(layers)):
                imageSources[axis].append(createImageSource( layers[layeridx], array2dsrcs[layeridx][axis] ))

        # three ortho image scenes
        self.imageScenes = []
        self.imageScenes.append(ImageScene2D())
        self.imageScenes.append(ImageScene2D())
        self.imageScenes.append(ImageScene2D())
        for i in xrange(3):
            self.imageScenes[i].imageSources = imageSources[i]


        # three ortho image views
        self.imageViews = []
        self.imageViews.append(ImageView2D(self._drawManager, self.imageScenes[0], useGL=useGL))
        self.imageViews.append(ImageView2D(self._drawManager, self.imageScenes[1], useGL=useGL))
        self.imageViews.append(ImageView2D(self._drawManager, self.imageScenes[2], useGL=useGL))

        for i in xrange(3):
            self.imageViews[i].drawing.connect(partial(self.updateLabels, axis=i))
            self.imageViews[i].customContextMenuRequested.connect(self.onCustomContextMenuRequested)

        # navigation control
        self.posModel     = PositionModel(self._shape)
        self.navCtrl      = NavigationControler(self.imageViews, self.sliceSources, self.posModel)
        self.navInterpret = NavigationInterpreter(self.posModel)

        # Add label widget to toolBoxLayout
        self.labelWidget = None
        
        # some auxiliary stuff
        self.focusAxis =  0 #the currently focused axis
        
        self._initConnects()

    def _initConnects(self):
        for i, v in enumerate(self.imageViews):
            #connect interpreter
            v.shape  = self.posModel.sliceShape(axis=i)
            v.mouseMoved.connect(partial(self.navInterpret.positionCursor, axis=i))
            v.mouseDoubleClicked.connect(partial(self.navInterpret.positionSlice, axis=i))
            v.changeSliceDelta.connect(partial(self.navInterpret.changeSliceRelative, axis=i))
            
        #connect controler
        self.posModel.channelChanged.connect(self.navCtrl.changeChannel)
        self.posModel.timeChanged.connect(self.navCtrl.changeTime)
        self.posModel.slicingPositionChanged.connect(self.navCtrl.moveSlicingPosition)
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)

    def setDrawingEnabled(self, enabled): 
        for i in range(3):
            self.imageViews[i].drawingEnabled = enabled

    def onCustomContextMenuRequested(self, pos):
        print "Volumeeditor.onCustomContextMenuRequested"
        self.customContextMenuRequested.emit(pos)
        
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

    #===========================================================================
    # View & Tools Options
    #===========================================================================
    def nextChannel(self):
        self.posModel.channel = self.posModel.channel+1

    def previousChannel(self):
        self.posModel.channel = self.posModel.channel-1
          
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

    def beginDraw(self, pos, axis):
        print "beginDraw: I'm doing nothing. Fixme or deleteme"
        
    def endDraw(self, pos, axis):
        result = self._drawManager.endDrawing(pos)
        print "endDraw: result =", result
        self.updateLabels(pos, axis)
        #FIXME
        #self.pushLabelsToLabelWidget()

    def pushLabelsToLabelWidget(self):
        #FIXME
        newLabels = self.getPendingLabels()
        self.labelWidget.labelMgr.newLabels(newLabels)
        
    def updateLabels(self, mousePos, axis):
        print "Volumeeditor.updateLabels"
        result = self._drawManager.dumpDraw(mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self._drawManager.drawnNumber
        labels = numpy.where(labels > 0, number, 0)
        import time, vigra
        vigra.impex.writeImage(labels, str(time.time()) + ".png")
#FIXME: resurrect
#        ls = LabelState('drawing', axis, self._viewManager.slicePosition[axis], \
#                        result[0:2], labels.shape, self._viewManager.time, self, \
#                        self._drawManager.erasing, labels, number)
#        self._history.append(ls)        
#        self.setLabels(result[0:2], axis, self._viewManager.slicePosition[axis], labels, self._drawManager.erasing)
        
    def getPendingLabels(self):
        temp = self._pendingLabels
        self._pendingLabels = []
        return temp

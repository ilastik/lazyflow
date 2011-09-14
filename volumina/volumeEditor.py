from PyQt4.QtCore import Qt, pyqtSignal, QObject
from PyQt4.QtGui import QApplication, QWidget, QBrush, QPen, QColor, QTransform

import copy
from functools import partial

from eventswitch import EventSwitch
from imageScene2D import ImageScene2D
from imageView2D import ImageView2D
from positionModel import PositionModel
from navigationControler import NavigationControler, NavigationInterpreter
from brushingcontroler import BrushingInterpreter, BrushingControler
from brushingmodel import BrushingModel
from pixelpipeline.imagepump import ImagePump
from slicingtools import SliceProjection

useVTK = True
try:
    from view3d.view3d import OverviewScene
except:
    import traceback
    traceback.print_exc()
    useVTK = False

#*******************************************************************************
# V o l u m e E d i t o r                                                      *
#*******************************************************************************

class VolumeEditor( QObject ):
    changedSlice      = pyqtSignal(int,int)
    onOverlaySelected = pyqtSignal(int)
    newLabelsPending  = pyqtSignal()
    
    zoomInFactor  = 1.1
    zoomOutFactor = 0.9

    def __init__( self, shape, layerStackModel, labelsink=None):
        super(VolumeEditor, self).__init__()
        assert(len(shape) == 5)
        self._shape = shape
        
        self._showDebugPatches = False

        #this setting controls the rescaling of the displayed _data to the full 0-255 range
        self.normalizeData = False

        #this settings controls the timer interval during interactive mode
        #set to 0 to wait for complete brushstrokes !
        #self.drawUpdateInterval = 300

        self.layerStack = layerStackModel

        self._pendingLabels = []

        # three ortho image pumps
        alongTXC = SliceProjection( abscissa = 2, ordinate = 3, along = [0,1,4] )
        alongTYC = SliceProjection( abscissa = 1, ordinate = 3, along = [0,2,4] )
        alongTZC = SliceProjection( abscissa = 1, ordinate = 2, along = [0,3,4] )

        imagepumps = []
        imagepumps.append(ImagePump( layerStackModel, alongTXC ))
        imagepumps.append(ImagePump( layerStackModel, alongTYC ))
        imagepumps.append(ImagePump( layerStackModel, alongTZC ))

        # synced slicesource collections
        syncedSliceSources = []
        for i in xrange(3):
            syncedSliceSources.append(imagepumps[i].syncedSliceSources)

        # three ortho image scenes
        self.imageScenes = []
        self.imageScenes.append(ImageScene2D())
        self.imageScenes.append(ImageScene2D())
        self.imageScenes.append(ImageScene2D())
        names = ['x', 'y', 'z']
        for scene, name, pump in zip(self.imageScenes, names, imagepumps):
            scene.setObjectName(name)
            scene.stackedImageSources = pump.stackedImageSources

        # three ortho image views
        self.imageViews = []
        self.imageViews.append(ImageView2D(self.imageScenes[0]))
        self.imageViews.append(ImageView2D(self.imageScenes[1]))
        self.imageViews.append(ImageView2D(self.imageScenes[2]))
        
        self.imageViews[0].setTransform(QTransform(1,0,0,0,1,0,0,0,1))
        self.imageViews[1].setTransform(QTransform(0,1,1,0,0,0))
        self.imageViews[2].setTransform(QTransform(0,1,1,0,0,0))

        if useVTK:
            self.view3d = OverviewScene(shape=self._shape[1:4])
            def onSliceDragged(num, pos):
                newPos = copy.deepcopy(self.posModel.slicingPos)
                newPos[pos] = num
                self.posModel.slicingPos = newPos
                
            self.view3d.changedSlice.connect(onSliceDragged)
        else:
            self.view3d = QWidget()

        for i in xrange(3):
            self.imageViews[i].customContextMenuRequested.connect(self.onCustomContextMenuRequested)


        # navigation control
        self.posModel     = PositionModel(self._shape)
        v3d = None
        if useVTK:
            v3d = self.view3d
        self.navCtrl      = NavigationControler(self.imageViews, syncedSliceSources, self.posModel, view3d=v3d)
        self.navInterpret = NavigationInterpreter(self.posModel, self.imageViews)

        # eventswitch
        self.es = EventSwitch(self.imageViews)
        self.es.interpreter = self.navInterpret

        # Add label widget to toolBoxLayout
        self.labelWidget = None
        
        # some auxiliary stuff
        self.focusAxis =  0 #the currently focused axis
        
        self.brushingModel = BrushingModel()
        #self.crosshairControler = CrosshairControler() 
        self.brushingInterpreter = BrushingInterpreter(self.brushingModel, self.imageViews)
        self.brushingControler = BrushingControler(self.brushingModel, self.posModel, labelsink)
        
        def onBrushSize(s):
            b = QPen(QBrush(self.brushingModel.drawColor), s)
            #b = QPen(QBrush(QColor(0,255,0)), 15) #for testing
            for s in self.imageScenes:
                s.setBrush(b)
        def onBrushColor(c):
            b = QPen(QBrush(c), self.brushingModel.brushSize)
            #b = QPen(QBrush(QColor(0,255,0)), 15) #for testing
            for s in self.imageScenes:
                s.setBrush(b)
        
        self.brushingModel.brushSizeChanged.connect(onBrushSize)
        self.brushingModel.brushColorChanged.connect(onBrushColor)
        
        self._initConnects()

    @property
    def showDebugPatches(self):
        return self._showDebugPatches
    @showDebugPatches.setter
    def showDebugPatches(self, show):
        for s in self.imageScenes:
            s.showDebugPatches = show
        self._showDebugPatches = show

    def scheduleSlicesRedraw(self):
        for s in self.imageScenes:
            s._invalidateRect()

    def _initConnects(self):
        for i, v in enumerate(self.imageViews):
            #connect interpreter
            v.sliceShape = self.posModel.sliceShape(axis=i)
            v.mouseMoved.connect(partial(self.navInterpret.positionCursor, axis=i))
            v.mouseDoubleClicked.connect(partial(self.navInterpret.positionSlice, axis=i))
            v.changeSliceDelta.connect(partial(self.navInterpret.changeSliceRelative, axis=i))
            
        #connect controler
        self.posModel.channelChanged.connect(self.navCtrl.changeChannel)
        self.posModel.timeChanged.connect(self.navCtrl.changeTime)
        self.posModel.slicingPositionChanged.connect(self.navCtrl.moveSlicingPosition)
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
        self.posModel.slicingPositionSettled.connect(self.navCtrl.settleSlicingPosition)

    def setDrawingEnabled(self, enabled): 
        for i in range(3):
            self.imageViews[i].drawingEnabled = enabled

    def onCustomContextMenuRequested(self, pos):
        print "Volumeeditor.onCustomContextMenuRequested"
        #self.customContextMenuRequested.emit(pos)
        
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
        #Implementing the wheel event for the whole 'volumina' widget
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

    def pushLabelsToLabelWidget(self):
        #FIXME
        newLabels = self.getPendingLabels()
        self.labelWidget.labelMgr.newLabels(newLabels)
        
    def getPendingLabels(self):
        temp = self._pendingLabels
        self._pendingLabels = []
        return temp

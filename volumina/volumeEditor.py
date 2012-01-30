import copy

from PyQt4.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt4.QtGui import QApplication, QWidget, QBrush, QPen, QColor, QTransform

import volumina
import volumina.pixelpipeline
import volumina.pixelpipeline.imagepump
from eventswitch import EventSwitch
from imageScene2D import ImageScene2D
from imageView2D import ImageView2D
from positionModel import PositionModel
from navigationControler import NavigationControler, NavigationInterpreter
from brushingcontroler import BrushingInterpreter, BrushingControler
from brushingmodel import BrushingModel
from slicingtools import SliceProjection
from pixelpipeline.slicesources import SyncedSliceSources

useVTK = True
try:
    from view3d.view3d import OverviewScene
except ImportError:
    import traceback
    traceback.print_exc()
    useVTK = False

#*******************************************************************************
# V o l u m e E d i t o r                                                      *
#*******************************************************************************

class VolumeEditor( QObject ):
    newImageView2DFocus = pyqtSignal()
    shapeChanged = pyqtSignal()

    @property
    def showDebugPatches(self):
        return self._showDebugPatches
    @showDebugPatches.setter
    def showDebugPatches(self, show):
        for s in self.imageScenes:
            s.showDebugPatches = show
        self._showDebugPatches = show
        
    def lastImageViewFocus(self, axis):
        self._lastImageViewFocus = axis
        self.newImageView2DFocus.emit()

    @property
    def dataShape(self):
        return self.posModel.shape5D

    @dataShape.setter
    def dataShape(self, s):
        self.posModel.shape5D = s
        for i, v in enumerate(self.imageViews):
            v.sliceShape = self.posModel.sliceShape(axis=i)
        self.view3d.dataShape = s[1:4]
        self.shapeChanged.emit()

    def __init__( self, layerStackModel, labelsink=None, parent=None):
        super(VolumeEditor, self).__init__(parent=parent)

        ##
        ## properties
        ##
        self._showDebugPatches = False
        self._lastImageViewFocus = None

        ##
        ## base components
        ##
        self.layerStack = layerStackModel
        self.imageScenes = [ImageScene2D(), ImageScene2D(), ImageScene2D()]
        self.imageViews = [ImageView2D(self.imageScenes[i]) for i in [0,1,2]]
        self.imageViews[0].focusChanged.connect(lambda arg=0 : self.lastImageViewFocus(arg))
        self.imageViews[1].focusChanged.connect(lambda arg=1 : self.lastImageViewFocus(arg))
        self.imageViews[2].focusChanged.connect(lambda arg=2 : self.lastImageViewFocus(arg)) 
        
        self.imagepumps = self._initImagePumps()

        self.posModel = PositionModel()
        self.brushingModel = BrushingModel()

        self.view3d = self._initView3d() if useVTK else QWidget()

        names = ['x', 'y', 'z']
        for scene, name, pump in zip(self.imageScenes, names, self.imagepumps):
            scene.setObjectName(name)
            scene.stackedImageSources = pump.stackedImageSources

        ##
        ## interaction
        ##
        # event switch
        self.eventSwitch = EventSwitch(self.imageViews)

        # navigation control
        v3d = self.view3d if useVTK else None
        syncedSliceSources = [self.imagepumps[i].syncedSliceSources for i in [0,1,2]]
        self.navCtrl      = NavigationControler(self.imageViews, syncedSliceSources, self.posModel, view3d=v3d)
        self.navInterpret = NavigationInterpreter(self.navCtrl)

        # brushing control
        #self.crosshairControler = CrosshairControler() 
        self.brushingControler = BrushingControler(self.brushingModel, self.posModel, labelsink)        
        self.brushingInterpreter = BrushingInterpreter(self.navCtrl, self.brushingControler)

        # initial interaction mode
        self.eventSwitch.interpreter = self.navInterpret

        ##
        ## connect
        ##
        self.posModel.channelChanged.connect(self.navCtrl.changeChannel)
        self.posModel.timeChanged.connect(self.navCtrl.changeTime)
        self.posModel.slicingPositionChanged.connect(self.navCtrl.moveSlicingPosition)
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
        self.posModel.slicingPositionSettled.connect(self.navCtrl.settleSlicingPosition)
        
        ##
        ## Other
        ##
        self.imageViews[0].setTransform(QTransform(1,0,0,0,1,0,0,0,1))
        self.imageViews[1].setTransform(QTransform(0,1,1,0,0,0))
        self.imageViews[2].setTransform(QTransform(0,1,1,0,0,0))

        #make sure that exactly one of the three slice views has focus
        #when the program starts up
        # -- unfortunately, this makes the VolumeEditorWidget crash in
        #    Qt Designer
        #def initialFocus():
        #    self.imageViews[0].setFocus(Qt.MouseFocusReason);
        #QTimer.singleShot(0,initialFocus)

    def scheduleSlicesRedraw(self):
        for s in self.imageScenes:
            s._invalidateRect()
        
    def setInteractionMode( self, name):
        modes = {'navigation': self.navInterpret, 'brushing': self.brushingInterpreter}
        self.eventSwitch.interpreter = modes[name]

    def cleanUp(self):
        QApplication.processEvents()
        for scene in self._imageViews:
            scene.close()
            scene.deleteLater()
        self._imageViews = []
        QApplication.processEvents()
    
    def closeEvent(self, event):
        event.accept()

    def nextChannel(self):
        assert(False)
        self.posModel.channel = self.posModel.channel+1

    def previousChannel(self):
        assert(False)
        self.posModel.channel = self.posModel.channel-1

    ##
    ## private
    ##
    def _initImagePumps( self ):
        alongTXC = SliceProjection( abscissa = 2, ordinate = 3, along = [0,1,4] )
        alongTYC = SliceProjection( abscissa = 1, ordinate = 3, along = [0,2,4] )
        alongTZC = SliceProjection( abscissa = 1, ordinate = 2, along = [0,3,4] )

        imagepumps = []
        imagepumps.append(volumina.pixelpipeline.imagepump.ImagePump( self.layerStack, alongTXC ))
        imagepumps.append(volumina.pixelpipeline.imagepump.ImagePump( self.layerStack, alongTYC ))
        imagepumps.append(volumina.pixelpipeline.imagepump.ImagePump( self.layerStack, alongTZC ))
        return imagepumps

    def _initView3d( self ):
        view3d = OverviewScene()
        def onSliceDragged(num, pos):
            newPos = copy.deepcopy(self.posModel.slicingPos)
            newPos[pos] = num
            self.posModel.slicingPos = newPos
        view3d.changedSlice.connect(onSliceDragged)
        return view3d


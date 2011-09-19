import copy

from PyQt4.QtCore import Qt, pyqtSignal, QObject
from PyQt4.QtGui import QApplication, QWidget, QBrush, QPen, QColor, QTransform

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
    @property
    def showDebugPatches(self):
        return self._showDebugPatches
    @showDebugPatches.setter
    def showDebugPatches(self, show):
        for s in self.imageScenes:
            s.showDebugPatches = show
        self._showDebugPatches = show

    def __init__( self, shape, layerStackModel, labelsink=None):
        super(VolumeEditor, self).__init__()
        assert(len(shape) == 5)

        ##
        ## properties
        ##
        self._shape = shape        
        self._showDebugPatches = False

        ##
        ## base components
        ##
        self.layerStack = layerStackModel
        self.imageScenes = [ImageScene2D(), ImageScene2D(), ImageScene2D()]
        self.imageViews = [ImageView2D(self.imageScenes[i]) for i in [0,1,2]]
        self.imagepumps = self._initImagePumps()

        self.posModel = PositionModel(self._shape)
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
        self.navCtrl      = NavigationControler(self.imageViews, syncedSliceSources, self.posModel, self.brushingModel, view3d=v3d)
        self.navInterpret = NavigationInterpreter(self.navCtrl)

        # brushing control
        #self.crosshairControler = CrosshairControler() 
        self.brushingInterpreter = BrushingInterpreter(self.navInterpret, self.navCtrl)
        self.brushingControler = BrushingControler(self.brushingModel, self.posModel, labelsink)        

        # initial interaction mode
        self.eventSwitch.interpreter = self.brushingInterpreter

        ##
        ## connect
        ##
        for i, v in enumerate(self.imageViews):
            v.sliceShape = self.posModel.sliceShape(axis=i)
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

    def scheduleSlicesRedraw(self):
        for s in self.imageScenes:
            s._invalidateRect()

    def setDrawingEnabled(self, enabled): 
        self.navCtrl.drawingEnabled = enabled
        
    def cleanUp(self):
        QApplication.processEvents()
        print "VolumeEditor: cleaning up "
        for scene in self._imageViews:
            scene.close()
            scene.deleteLater()
        self._imageViews = []
        QApplication.processEvents()
        print "finished saving thread"
    
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
        imagepumps.append(ImagePump( self.layerStack, alongTXC ))
        imagepumps.append(ImagePump( self.layerStack, alongTYC ))
        imagepumps.append(ImagePump( self.layerStack, alongTZC ))
        return imagepumps

    def _initView3d( self ):
        view3d = OverviewScene(shape=self._shape[1:4])
        def onSliceDragged(num, pos):
            newPos = copy.deepcopy(self.posModel.slicingPos)
            newPos[pos] = num
            self.posModel.slicingPos = newPos
        view3d.changedSlice.connect(onSliceDragged)
        return view3d


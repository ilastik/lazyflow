from PyQt4.QtCore import QObject

from singlesplitter import EventSwitch
from imageScene2D import ImageScene2D
from imageView2D import ImageView2D
from singlesplitter import PositionModel
from singlesplitter import NavigationControler, NavigationInterpreter
from brushingcontroler import BrushingInterpreter, BrushingControler
from brushingmodel import BrushingModel
from pixelpipeline.imagepump import ImagePump
from slicingtools import SliceProjection
from numpy import zeros

useVTK = True
try:
    from view3d.view3d import OverviewScene
except:
    import traceback
    traceback.print_exc()
    useVTK = False

#*******************************************************************************
# I m a g e E d i t o r                                                      *
#*******************************************************************************

class ImageEditor( QObject ):
        

    def __init__( self, shape, layerStackModel, labelsink=None):
        super(ImageEditor, self).__init__()
        assert(len(shape) == 5)

        ##
        ## properties
        ##
        self._shape = shape        
        

        ##
        ## base components, intiation
        ##
        self.layerStack = layerStackModel
        self.imageScene = ImageScene2D()
        self.imageView = ImageView2D(self.imageScene)
        self.imagepump = self._initImagePump()
        self.posModel = PositionModel(self._shape)
        self.brushingModel = BrushingModel()
        self.imageScene.stackedImageSources = self.imagepump.stackedImageSources
        
        ##
        ## interaction
        ##
        # event switch
        self.eventSwitch = EventSwitch(self.imageView)

        # navigation control
        v3d = self.view3d if useVTK else None
        syncedSliceSources = self.imagepump.syncedSliceSources 
        self.navCtrl      = NavigationControler(self.imageView, syncedSliceSources, self.posModel, self.brushingModel, view3d=v3d)
        self.navInterpret = NavigationInterpreter(self.navCtrl)

        # initial interaction mode
        self.eventSwitch.interpreter = self.navInterpret

        ##
        ## connect
        ##  
        self.imageView.sliceShape=self.posModel.sliceShape(0) 
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
        
        
        
    ##
    ## private
    ##
    def _initImagePump( self ):
        
        #IDEA: Make function that determines SliceProjection for any given Array
        alongTXC = SliceProjection( abscissa = 2, ordinate = 3, along = [0,1,4] )    
        imagepump = ImagePump( self.layerStack, alongTXC )
        return imagepump
    

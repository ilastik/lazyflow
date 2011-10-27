from PyQt4.QtCore import QObject    
from imageScene2D import ImageScene2D
from imageView2D import ImageView2D
from singlesplitter import  PositionModel, NavigationControler, NavigationInterpreter, \
                            EventSwitch
from brushingmodel import BrushingModel
from pixelpipeline.imagepump import ImagePump
from slicingtools import SliceProjection
from pixelpipeline.datasources import ArraySource
from volumina.layer import GrayscaleLayer
from volumina.layerstack import LayerStackModel


useVTK = True
try:
    from view3d.view3d import OverviewScene
except:
    import traceback
    traceback.print_exc()
    useVTK = False

#*******************************************************************************
# I m a g e E d i t o r                                                        *
#*******************************************************************************

class ImageEditor( QObject ):
        

    def __init__( self, shape = None, layerStackModel = None):
        super(ImageEditor, self).__init__()
        
        
        self._shape = shape        
        self._layerStack = layerStackModel  
        self.imageScene = ImageScene2D()
        self.posModel = PositionModel(self._shape)
        self.imagepump = self._initImagePump()
        self.imageScene.stackedImageSources = self.imagepump.stackedImageSources
        self.imageView = ImageView2D(self.imageScene)
        
        self.brushingModel = BrushingModel()
        
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
        self.imageView.sliceShape=self._shape
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
        
        
        
    ##
    ## private
    ##
    def _initImagePump( self ):
        
        TwoDProjection = SliceProjection(0,1,[])
        imagepump = ImagePump( self._layerStack, TwoDProjection )
        return imagepump
    

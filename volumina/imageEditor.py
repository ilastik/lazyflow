from PyQt4.QtCore import QObject    
from imageScene2D import ImageScene2D
from imageEditorComponents import  PositionModel, NavigationControler,  \
                                   NavigationInterpreter, ImageView2D
from eventswitch import EventSwitch
from brushingmodel import BrushingModel
from pixelpipeline.imagepump import ImagePump
from slicingtools import SliceProjection

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
        self.imageView = [ImageView2D(self.imageScene)]
        self.brushingModel = BrushingModel()
        
        ##
        ## interaction
        ##
        # event switch
        self.eventSwitch = EventSwitch(self.imageView)

        # navigation control
        syncedSliceSources = self.imagepump.syncedSliceSources 
        self.navCtrl      = NavigationControler(self.imageView[0], syncedSliceSources, self.posModel, self.brushingModel)
        self.navInterpret = NavigationInterpreter(self.navCtrl)

        # initial interaction mode
        self.eventSwitch.interpreter = self.navInterpret

        ##
        ## connect
        ##  
        self.imageView[0].sliceShape=self._shape
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
        
        
        
    ##
    ## private
    ##
    def _initImagePump( self ):
        
        TwoDProjection = SliceProjection(0,1,[])
        imagepump = ImagePump( self._layerStack, TwoDProjection )
        return imagepump
    

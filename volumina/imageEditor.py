from PyQt4.QtCore import QObject    
from imageScene2D import ImageScene2D
from imageEditorComponents import  PositionModelImage, \
    NavigationControlerImage, NavigationInterpreterImage
from eventswitch import EventSwitch
from brushingmodel import BrushingModel
import volumina.pixelpipeline.imagepump
from slicingtools import SliceProjection
from imageView2D import ImageView2D

#*******************************************************************************
# I m a g e E d i t o r                                                        *
#*******************************************************************************

class ImageEditor( QObject ):

    def __init__( self, layerStackModel = None):
        super(ImageEditor, self).__init__()
        
        self._shape = None        
        self._layerStack = layerStackModel  
        self.imageScene = ImageScene2D()
        self.posModel = PositionModelImage()
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
        self.navCtrl      = NavigationControlerImage(self.imageView[0], syncedSliceSources, self.posModel, self.brushingModel)
        self.navInterpret = NavigationInterpreterImage(self.navCtrl)

        # initial interaction mode
        self.eventSwitch.interpreter = self.navInterpret

        ##
        ## connect
        ##  
        self.posModel.cursorPositionChanged.connect(self.navCtrl.moveCrosshair)
   
    @property
    def dataShape(self):
        return self.posModel._shape2D
    @dataShape.setter
    def dataShape(self, s):
        assert len(s) == 2, "got a non-2D shape '%r'" % (s,)
        self.posModel.shape = s
        self.imageView[0].sliceShape = s

    ##
    ## private
    ##
    def _initImagePump( self ):
        
        TwoDProjection = SliceProjection(0,1,[])
        imagepump = volumina.pixelpipeline.imagepump.ImagePump( self._layerStack, TwoDProjection )
        return imagepump
    

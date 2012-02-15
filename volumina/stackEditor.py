from slicingtools import SliceProjection
from layerstack import LayerStackModel
from pixelpipeline.imagepump import ImagePump

class StackPositionModel( object ):
    def __init__( self ):
        self._through = 0

alongTZC = SliceProjection( abscissa = 1, ordinate = 2, along = [0,3,4] )
class StackEditor( object ):
    def __init__( self, layerStackModel = LayerStackModel(), sliceProjection = alongTZC ):
        self.layerStackModel = layerStackModel
        self.imagePump = ImagePump( layerStackModel, sliceProjection )
        self.positionModel = StackPositionModel()

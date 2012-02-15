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

if __name__ == "__main__":
    import numpy as np
    from pixelpipeline.datasources import ArraySource
    from volumina.layer import GrayscaleLayer
    data = np.random.random_integers(0,255, size= (512,512,128))
    ds = ArraySource(data)
    
    se = StackEditor()
    se.layerStackModel.append(GrayscaleLayer(ds))

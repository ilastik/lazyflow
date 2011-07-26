from multimethods import multimethod
import layer
from pixelpipeline.imagesources import GrayscaleImageSource, RGBAImageSource

@multimethod(layer.GrayscaleLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    return GrayscaleImageSource( datasources2d[0] )

@multimethod(layer.RGBALayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 4
    ds = datasources2d
    return RGBAImageSource( ds[0], ds[1], ds[2], ds[3] )

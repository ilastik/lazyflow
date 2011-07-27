from multimethods import multimethod
import layer
from pixelpipeline.imagesources import GrayscaleImageSource, RGBAImageSource
from pixelpipeline.datasources import ConstantSource

@multimethod(layer.GrayscaleLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    return GrayscaleImageSource( datasources2d[0] )

@multimethod(layer.RGBALayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 4
    ds = datasources2d
    for i in xrange(3):
        if datasources2d[i] == None:
            ds[i] = ConstantSource(layer.color_missing_value)
    if datasources2d[3] == None:
        ds[3] = ConstantSource(layer.alpha_missing_value)
    return RGBAImageSource( ds[0], ds[1], ds[2], ds[3] )

import copy
from volumeeditor.pixelpipeline.multimethods import multimethod
from volumeeditor.layer import GrayscaleLayer, RGBALayer
from imagesources import GrayscaleImageSource, RGBAImageSource
from datasources import ConstantSource

@multimethod(GrayscaleLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    return GrayscaleImageSource( datasources2d[0] )

@multimethod(RGBALayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 4
    ds = copy.copy(datasources2d)
    for i in xrange(3):
        if datasources2d[i] == None:
            ds[i] = ConstantSource(layer.color_missing_value)
    if datasources2d[3] == None:
        ds[3] = ConstantSource(layer.alpha_missing_value)
    return RGBAImageSource( ds[0], ds[1], ds[2], ds[3] )

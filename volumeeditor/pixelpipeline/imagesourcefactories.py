import copy
from volumeeditor.pixelpipeline.multimethods import multimethod
from volumeeditor.layer import GrayscaleLayer, RGBALayer, ColortableLayer, \
                               AlphaModulatedLayer
from imagesources import GrayscaleImageSource, ColortableImageSource, \
                         RGBAImageSource, AlphaModulatedImageSource
from datasources import ConstantSource

@multimethod(AlphaModulatedLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    src = AlphaModulatedImageSource( datasources2d[0], layer )
    src.setObjectName(layer.name)
    layer.nameChanged.connect(lambda x: src.setObjectName(str(x)))
    layer.tintColorChanged.connect(lambda: src.setDirty((slice(None,None), slice(None,None))))
    return src

@multimethod(GrayscaleLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    src = GrayscaleImageSource( datasources2d[0], layer )
    src.setObjectName(layer.name)
    layer.nameChanged.connect(lambda x: src.setObjectName(str(x)))
    layer.thresholdingChanged.connect(lambda: src.setDirty((slice(None,None), slice(None,None))))
    return src

@multimethod(ColortableLayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 1
    src = ColortableImageSource( datasources2d[0], layer.colorTable )
    src.setObjectName(layer.name)
    layer.nameChanged.connect(lambda x: src.setObjectName(str(x)))
    return src

@multimethod(RGBALayer, list)
def createImageSource( layer, datasources2d ):
    assert len(datasources2d) == 4
    ds = copy.copy(datasources2d)
    for i in xrange(3):
        if datasources2d[i] == None:
            ds[i] = ConstantSource(layer.color_missing_value)
    if datasources2d[3] == None:
        ds[3] = ConstantSource(layer.alpha_missing_value)
    src = RGBAImageSource( ds[0], ds[1], ds[2], ds[3], layer )
    src.setObjectName(layer.name)
    layer.nameChanged.connect(lambda x: src.setObjectName(str(x)))
    layer.thresholdingChanged.connect(lambda: src.setDirty((slice(None,None), slice(None,None))))
    return src

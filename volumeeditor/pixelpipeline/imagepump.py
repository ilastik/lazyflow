from functools import partial
from PyQt4.QtCore import QObject, pyqtSignal, QRect
from slicesources import SliceSource, SyncedSliceSources
from imagesourcefactories import createImageSource

class StackedImageSources( QObject ):
    isDirty      = pyqtSignal( QRect )
    stackChanged = pyqtSignal()

    def __init__( self, layerStackModel ):
        super(StackedImageSources, self).__init__()
        self._layerStackModel = layerStackModel
        self._layerToIms = {}
        self._curryRegistry = {}
        layerStackModel.orderChanged.connect( self.stackChanged )

    def __len__( self ):
        return reduce( lambda cum, x: cum + 1, self, 0)

    def __iter__( self ):
        for layer in self._layerStackModel.layerStack:
            if layer.visible and layer in self._layerToIms:
                yield (layer.opacity, self._layerToIms[layer])

    def __getitem__(self, i):
        l = [layer for layer in self._layerStackModel.layerStack if layer.visible]
        return l[i]  

    def register( self, layer, imageSource ):
        assert not layer in self._layerToIms, "layer %s already registered" % str(layer)
        self._layerToIms[layer] = imageSource
        imageSource.isDirty.connect(self.isDirty)
        self._curryRegistry[layer] = partial(self._onOpacityChanged, layer)
        layer.opacityChanged.connect( self._curryRegistry[layer] )
        layer.visibleChanged.connect( self._onVisibleChanged )
        self.stackChanged.emit()

    def deregister( self, layer ):
        assert layer in self._layerToIms, "layer %s is not registered; can't be deregistered" % str(layer)
        ims = self._layerToIms[layer]
        ims.isDirty.disconnect( self.isDirty)
        layer.opacityChanged.disconnect( self._curryRegistry[layer] )
        layer.visibleChanged.disconnect( self._onVisibleChanged )
        del self._curryRegistry[layer]
        del self._layerToIms[layer]
        self.stackChanged.emit()

    def _onOpacityChanged( self, layer, opacity ):
        if layer.visible:
            self.isDirty.emit( QRect() )

    def _onVisibleChanged( self, visible ):
        self.isDirty.emit( QRect() )



#*******************************************************************************
# I m a g e P u m p                                                            *
#*******************************************************************************

class ImagePump( object ):
    @property
    def syncedSliceSources( self ):
        return self._syncedSliceSources

    @property
    def stackedImageSources( self ):
        return self._stackedImageSources

    def __init__( self, layerStackModel, sliceProjection ):
        super(ImagePump, self).__init__()
        self._layerStackModel = layerStackModel
        self._projection = sliceProjection
        self._layerToSliceSrcs = {}
    
        ## setup image source stack and slice sources
        self._stackedImageSources = StackedImageSources( layerStackModel )
        slicesrcs = []
        for layer in layerStackModel.layerStack:
            sliceSources, imageSource = self._parseLayer(layer)
            slicesrcs.extend(sliceSources)
            self._layerToSliceSrcs[layer] = sliceSources
            self._stackedImageSources.register(layer, imageSource)
        self._syncedSliceSources = SyncedSliceSources( slicesrcs )

        def onLayersAboutToBeRemoved( parent, start, end):
            for i in xrange(start, end + 1):
                layer = self._layerStackModel.layerStack[i]
                self._stackedImageSources.deregister(layer)
                for ss in self._layerToSliceSrcs[layer]:
                    self._syncedSliceSources.remove(ss)
                del self._layerToSliceSrcs[layer]                
        layerStackModel.rowsAboutToBeRemoved.connect(onLayersAboutToBeRemoved)

    def _parseLayer( self, layer ):
        def sliceSrcOrNone( datasrc ):
            if datasrc:
                return SliceSource( datasrc, self._projection )
            return None

        slicesrcs = map( sliceSrcOrNone, layer.datasources )
        ims = createImageSource( layer, slicesrcs )
        # remove Nones
        slicesrcs = [ src for src in slicesrcs if src != None]
        return slicesrcs, ims


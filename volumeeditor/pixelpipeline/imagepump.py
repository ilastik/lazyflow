from PyQt4.QtCore import pyqtSignal, QRect, QObject
from slicesources import SliceSource, SyncedSliceSources
from imagesourcefactories import createImageSource

class ImagePump( QObject ):
    #isDirty = pyqtSignal( QRect )
    
    @property
    def syncedSliceSources( self ):
        return self._syncedSliceSources

    def __init__( self, layerStackModel, sliceProjection ):
        self._imsStack = []
        self._syncedSliceSources = SyncedSliceSources()
        self._layerModel = layerStackModel
        self._projection = sliceProjection
        self._update()

    def __call__( self ):
        return self._imsStack

    def _update( self ):
        self._imsStack = []
        self._syncedSliceSources = SyncedSliceSources()
        for layerWrapper in self._layerModel.layerStack:
            self._appendLayer( layerWrapper.layer )

    def _appendLayer( self, layer ):
        def sliceSrcOrNone( datasrc ):
            if datasrc:
                return SliceSource( datasrc, self._projection )
            return None

        slicesrcs = map( sliceSrcOrNone, layer.datasources )
        ims = createImageSource( layer, slicesrcs )
        self._imsStack.append(( layer.opacity, ims ))
        for src in slicesrcs:
            if src:
                self._syncedSliceSources.add( src )

            

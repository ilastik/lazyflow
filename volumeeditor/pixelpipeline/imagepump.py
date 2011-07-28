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
        self._layerStack = layerStackModel
        self._projection = sliceProjection
        self._update()

    def __call__( self ):
        return self._imsStack

    def _update( self ):
        self._imsStack = []
        self._syncedSliceSources = SyncedSliceSources()
        for layer in self._layerStack.layers:
            self._appendLayer( layer )

    def _appendLayer( self, layer ):
        slicesrcs = [ SliceSource( src, self._projection ) for src in layer.datasources ]
        ims = createImageSource( layer, slicesrcs )
        self._imsStack.append(( layer.opacity, ims ))
        for src in slicesrc:
            self._syncedSliceSources.add( src )

            

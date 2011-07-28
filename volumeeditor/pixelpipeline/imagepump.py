from PyQt4.QtCore import pyqtSignal, QRect, QObject
from slicesources import SliceSource, SyncedSliceSources
from imagesourcefactories import createImageSource

from collections import namedtuple

ImageSourceStackEntry = namedtuple('ImageSourceStackEntry', 'opacity imageSource')


class ImagePump( QObject ):
    #isDirty = pyqtSignal( QRect )
    
    @property
    def imageSourceStack( self ):
        return self._imsStack

    @property
    def syncedSliceSources( self ):
        return self._syncedSliceSources

    def __init__( self, layers, sliceProjection ):
        self._imsStack = []
        self._syncedSliceSources = SyncedSliceSources()
        self._projection = sliceProjection

    def update( self, layers):
        '''
        for i, layer in layers:
            slicesrcs = []
            for datasrc in layer.datasources:
                

        self._imsStack = []
        self._syncedSliceSources = SyncedSliceSources()

        for layeridx in xrange(len(layerStack)):
            if layers[layeridx].visible:
                self._imsStack.append( ImageSourceStackEntry(layers[layeridx].opacity, imageSources[i][layeridx]))
        '''
        pass

    def _appendLayer( self, layer ):
        slicesrcs = [ SliceSource( src, self._projection ) for src in layer.datasources ]
        createImageSource( layer, slicesrcs )

            

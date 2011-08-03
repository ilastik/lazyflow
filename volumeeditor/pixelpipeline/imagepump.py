from functools import partial
from PyQt4.QtCore import QObject, pyqtSignal, QRect
from slicesources import SliceSource, SyncedSliceSources
from imagesourcefactories import createImageSource
from imsstack import ImsStack

class StackedImageSources( QObject ):
    isDirty = pyqtSignal( QRect )

    def __init__( self, layerStackModel, lseToIms ):
        super(StackedImageSources, self).__init__()
        self._layerStackModel = layerStackModel
        self._lseToIms = lseToIms
        for entry in self._layerStackModel.layerStack:
            layer = entry.layer
            layer.opacityChanged.connect( partial(self._onOpacityChanged, layer) )
            layer.visibleChanged.connect( self._onVisibleChanged )
        for ims in lseToIms.itervalues():
            ims.isDirty.connect(self.isDirty)

    def __iter__( self ):
        for entry in self._layerStackModel.layerStack:
            if entry.layer.visible:
                yield (entry.layer.opacity, self._lseToIms[entry])

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
        #LayerStackEntry to ImageSource mapping
        self._lseToIms = dict()
        self._layerStackModel = layerStackModel

        self._projection = sliceProjection
    
        ## setup image source stack and slice sources
        slicesrcs = []
        for layerStackEntry in layerStackModel.layerStack:
            sliceSources, imageSource = self._parseLayer(layerStackEntry.layer)
            slicesrcs.extend(sliceSources)
            self._lseToIms[layerStackEntry] = imageSource
        self._syncedSliceSources = SyncedSliceSources( slicesrcs )
        self._stackedImageSources = StackedImageSources( self._layerStackModel, self._lseToIms )

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


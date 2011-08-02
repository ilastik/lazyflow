from slicesources import SliceSource, SyncedSliceSources
from imagesourcefactories import createImageSource
from imsstack import ImsStack

#*******************************************************************************
# I m a g e P u m p                                                            *
#*******************************************************************************

class ImagePump( object ):
    @property
    def syncedSliceSources( self ):
        return self._syncedSliceSources

    @property
    def imsStack( self ):
        return self._imsStack

    def __init__( self, layerStackModel, sliceProjection ):
        self._layerModel = layerStackModel
        self._projection = sliceProjection
    
        ## setup image source stack and slice sources
        slicesrcs = []
        stack_entries = []
        for layerWrapper in self._layerModel.layerStack:
            srcs, entry = self._parseLayer(layerWrapper.layer)
            slicesrcs.extend(srcs)
            stack_entries.append(entry)
        self._syncedSliceSources = SyncedSliceSources( slicesrcs )
        self._imsStack = ImsStack( stack_entries )
        
        def dirty():
            print "ImagePump: setting image stack dirty"
            self._imsStack.setDirty()
        self._layerModel.orderChanged.connect(dirty)

    def _parseLayer( self, layer ):
        def sliceSrcOrNone( datasrc ):
            if datasrc:
                return SliceSource( datasrc, self._projection )
            return None

        slicesrcs = map( sliceSrcOrNone, layer.datasources )
        ims = createImageSource( layer, slicesrcs )
        stack_entry = ( layer.opacity, ims )
        # remove Nones
        slicesrcs = [ src for src in slicesrcs if src != None]
        return slicesrcs, stack_entry


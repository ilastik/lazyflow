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
        return self._layerStackModel.rowCount()

    def __iter__( self ):
        for layer in self._layerStackModel:
            yield (layer.opacity, layer.visible, self._layerToIms[layer])

    def __getitem__(self, i):
        return self._layerStackModel[i] 

    def register( self, layer, imageSource ):
        #print "<StackedImageSources.register(self=%r, layer=%r, imageSource=%r)>" % (self, layer, imageSource)
        assert not layer in self._layerToIms, "layer %s already registered" % str(layer)
        self._layerToIms[layer] = imageSource
        imageSource.isDirty.connect(self.isDirty)
        self._curryRegistry[layer] = partial(self._onOpacityChanged, layer)
        layer.opacityChanged.connect( self._curryRegistry[layer] )
        layer.visibleChanged.connect( self._onVisibleChanged )
        self.stackChanged.emit()
        #print "</StackedImageSources.register(self=%r)>" % (self)

    def deregister( self, layer ):
        #print "<StackedImageSources.deregister(self=%r, layer=%r)>" % (self, layer)
        assert layer in self._layerToIms, "layer %s is not registered; can't be deregistered" % str(layer)
        ims = self._layerToIms[layer]
        ims.isDirty.disconnect( self.isDirty)
        layer.opacityChanged.disconnect( self._curryRegistry[layer] )
        layer.visibleChanged.disconnect( self._onVisibleChanged )
        del self._curryRegistry[layer]
        del self._layerToIms[layer]
        self.stackChanged.emit()
        #print "</StackedImageSources.deregister(self=%r)>" % (self)

    def isRegistered( self, layer ):
        return layer in self._layerToIms

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
        self._syncedSliceSources = SyncedSliceSources()
        for layer in layerStackModel:
            self._addLayer( layer )

        ## handle layers removed from layerStackModel
        def onRowsAboutToBeRemoved( parent, start, end):
            #print "ImagePump.onRowsAboutToBeRemoved"
            for i in xrange(start, end + 1):
                layer = self._layerStackModel[i]
                self._removeLayer( layer )
        layerStackModel.rowsAboutToBeRemoved.connect(onRowsAboutToBeRemoved)

        ## handle new layers in layerStackModel
        def onDataChanged( startIndexItem, endIndexItem):
            start = startIndexItem.row()
            stop = endIndexItem.row() + 1
            #FIXME: the layerstackmodel seems to be wrongly implemented
            #       (we need a reverse sorting of the layer list, for which
            #        some hacks were introduced)
            #        the following loop is a necessary workaround for now.
            #for i in xrange(start, stop):
            for i in range(self._layerStackModel.rowCount()):
                layer = self._layerStackModel[i]
                # model implementation removes and adds the same layer instance to move selections up/down
                # therefore, check if the layer is already registered before adding as new
                if not self._stackedImageSources.isRegistered(layer): 
                    self._addLayer(layer)
        layerStackModel.dataChanged.connect(onDataChanged)


    def _createSources( self, layer ):
        def sliceSrcOrNone( datasrc ):
            if datasrc:
                return SliceSource( datasrc, self._projection )
            return None

        slicesrcs = map( sliceSrcOrNone, layer.datasources )
        ims = createImageSource( layer, slicesrcs )
        # remove Nones
        slicesrcs = [ src for src in slicesrcs if src != None]
        return slicesrcs, ims

    def _addLayer( self, layer ):
        #print "<ImagePump._addLayer(self=%r, layer=%r) >" % (self, layer)
        sliceSources, imageSource = self._createSources(layer)
        for ss in sliceSources:
            self._syncedSliceSources.add(ss)
        self._layerToSliceSrcs[layer] = sliceSources
        self._stackedImageSources.register(layer, imageSource)
        #print "</ImagePump._addLayer>(self=%r)>" % self

    def _removeLayer( self, layer ):
        #print "<ImagePump._removeLayer(self=%r, layer=%r) >" % (self, layer)
        self._stackedImageSources.deregister(layer)
        for ss in self._layerToSliceSrcs[layer]:
            self._syncedSliceSources.remove(ss)
        del self._layerToSliceSrcs[layer] 
        #print "</ImagePump._removeLayer(self=%r)>" % self               

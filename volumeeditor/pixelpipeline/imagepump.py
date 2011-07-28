from PyQt4.QtCore import pyqtSignal, QRect, QObject
from 

from collections import namedtuple

ImageSourceStackEntry = namedtuple('ImageSourceStackEntry', 'opacity imageSource')


class ImagePump( QObject ):
    isDirty = pyqtSignal( QRect )
    
    @property
    def imageSourceStack( self ):
        return self._imsStack

    @property
    def syncedSliceSources( self ):
        return self._syncedSliceSources

    def __init__( self, layerStack ):
        self._imsStack = None
        self._syncedSliceSources

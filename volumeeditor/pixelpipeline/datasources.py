from PyQt4.QtCore import QObject, pyqtSignal

class DataSource( QObject ):
    changed = pyqtSignal()

    def __init__( self, data ):
        super(DataSource, self).__init__()
        self._data = data

    def onOriginChanged( self ):
        self.changed.emit()
    
    def __getitem__( self, slicing):
        return self._data[slicing]

    def __setitem__( self, slicing, value ):
        self._data[slicing] = value
        self.changed.emit()

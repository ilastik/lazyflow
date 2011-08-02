from PyQt4.QtCore import QObject, pyqtSignal, QRect
class ImsStack( QObject ):
    ''' Stack of image sources with associated opacity values.

    Signals:
    changed -- entries in list were reordered, removed,
               added or replaced
    isDirty -- one of the contained image sources has emitted isDirty

    '''

    changed = pyqtSignal()
    isDirty = pyqtSignal( QRect )

    def __init__( self, list_of_opacity_ims_tuples = []):
        super(ImsStack, self).__init__()
        self._stack = list_of_opacity_ims_tuples
        # pass isDirty signals from all contained ims along
        for entry in self._stack:
            ims = entry[1]
            ims.isDirty.connect( self.isDirty )

    def __iter__( self ):
        return iter(self._stack)

    def __getitem__( self, key ):
        return self._stack[key]

    def __setitem__( self, key, value ):
        ims = self._stack[key][1]
        ims.isDirty.disconnect( self.isDirty )
        value[1].isDirty.connect( self.isDirty )
        self._stack[key] = value
        
        self.changed.emit()

    def __delitem__( self, key ):
        ims = self._stack[key][1]
        ims.isDirty.disconnect( self.isDirty )
        del self._stack[key]
        self.changed.emit()

    def __len__( self ):
        return len(self._stack)

    def set( self, other = [] ):
        '''Discard old stack and wrap another.'''
        for entry in self._stack:
            ims = entry[1]
            ims.isDirty.disconnect( self.isDirty )
        self._stack = other
        for entry in self._stack:
            ims = entry[1]
            ims.isDirty.connect( self.isDirty )
        self.changed.emit()

    def setDirty( self ):
        self.changed.emit()
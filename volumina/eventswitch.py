from PyQt4.QtCore import QObject

class EventSwitch( QObject ):
    @property
    def interpreter( self ):
        return self._interpreter

    @interpreter.setter
    def interpreter( self, interpreter ):
        for view in self._imageViews:
            view.removeEventFilter( self._interpreter )
            if interpreter:
                view.installEventFilter( interpreter )
        self._interpreter = interpreter

    def __init__( self, imageviews, interpreter=None):
        super(EventSwitch, self).__init__()
        self._imageViews = imageviews
        self._interpreter = None
        self.interpreter = interpreter

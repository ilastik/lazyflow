from PyQt4.QtCore import QObject

class EventSwitch( QObject ):
    def __init__( self, imageviews, interpreter ):
        super(EventSwitch, self).__init__()
        for view in imageviews:
            view.installEventFilter( interpreter )
        self._imageViews = imageviews
        self._interpreter = interpreter

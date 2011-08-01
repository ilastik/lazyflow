from PyQt4.QtCore import QObject

class EventSwitch( QObject ):
    def __init__( self, imageviews ):
        super(EventSwitch, self).__init__()
        for view in imageviews:
            view.scene().installEventFilter( self )
            view.viewport().installEventFilter( self )
            view.installEventFilter( self )
        self._imageViews = imageviews

    def eventFilter( self, watched, event ):
        print watched, event
        return False

if __name__ == '__main__':
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


    class MyWidget( QWidget ):
        pass

    app = QApplication([])

    w = MyWidget()
    wc = MyWidget(w)
    wc.show()
    w.show()
    es = EventSwitch( w )
    w.installEventFilter( es )


    app.exec_()

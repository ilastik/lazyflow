from PyQt4.QtCore import QPoint, QPointF, QTimer, pyqtSignal, Qt
from PyQt4.QtGui import QCursor, QGraphicsView, QPainter, QVBoxLayout, QApplication

import numpy

from crossHairCursor import CrossHairCursor
from sliceIntersectionMarker import SliceIntersectionMarker

#*******************************************************************************
# I m a g e V i e w 2 D                                                        *
#*******************************************************************************

class ImageView2D(QGraphicsView):
    focusChanged = pyqtSignal()
    """
    Shows a ImageScene2D to the user and allows for interactive
    scrolling, panning, zooming etc.

    """
    @property
    def sliceShape(self):
        """
        (width, height) of the scene.
        Specifying the shape is necessary to allow for correct
        scrollbars
        """
        return self._sliceShape
    @sliceShape.setter
    def sliceShape(self, s):
        self._sliceShape = s
        sceneShape = (s[1], s[0])
        self.scene().sceneShape                  = sceneShape
        self._crossHairCursor.sceneShape         = sceneShape
        self._sliceIntersectionMarker.sceneShape = sceneShape
           
    @property
    def hud(self):
        return self._hud
    @hud.setter
    def hud(self, hud):
        """
        Sets up a heads up display at the upper left corner of the view
        
        hud -- a QWidget
        """
        
        self._hud = hud
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self._hud)
        self.layout().addStretch()
    
    def __init__(self, imagescene2d):
        """
        Constructs a view upon a ImageScene2D
        
        imagescene2d -- a ImgeScene2D instance
        """
        
        QGraphicsView.__init__(self)
        self.setScene(imagescene2d)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._isRubberBandZoom = False
        self._cursorBackup = None
        
        #these attributes are exposed as public properties above
        self._sliceShape  = None #2D shape of this view's shown image
        self._slices = None #number of slices that are stacked
        self._hud    = None
        
        self._crossHairCursor         = None
        self._sliceIntersectionMarker = None

        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tickerEvent)
        
        #
        # Setup the Viewport for fast painting
        #
        #With these flags turned on we could handle the drawing of the
        #white background ourselves thus removing the flicker
        #when scrolling fast through the slices
        #self.viewport().setAttribute(Qt.WA_OpaquePaintEvent)
        #self.viewport().setAttribute(Qt.WA_NoSystemBackground)
        #self.viewport().setAttribute(Qt.WA_PaintOnScreen)
        #self.viewport().setAutoFillBackground(False)
        
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        #as rescaling images is slow if done in software,
        #we use Qt's built-in background caching mode so that the cached
        #image need only be blitted on the screen when we only move
        #the cursor
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHint(QPainter.Antialiasing, False)

        self._crossHairCursor = CrossHairCursor(self.scene())
        self._crossHairCursor.setZValue(99)
        
        self._sliceIntersectionMarker = SliceIntersectionMarker()
        self._sliceIntersectionMarker.setZValue(100)
        self.scene().addItem(self._sliceIntersectionMarker)
        #FIXME: Use a QAction here so that we do not have to synchronize
        #between this initial state and the toggle button's initial state
        if self._hud is not None:
            self._sliceIntersectionMarker.setVisibility(True)
 
        #FIXME: this should be private, but is currently used from
        #       within the image scene renderer
        self.tempImageItems = []
        
        self._zoomFactor = 1.0
        
        #for panning
        self._lastPanPoint = QPoint()
        self._dragMode = False
        self._deltaPan = QPointF(0,0)
        
        #Unfortunately, setting the style like this make the scroll bars look
        #really crappy...
        #self.setStyleSheet("QWidget:!focus { border: 2px solid " + self._axisColor[self._axis].name() +"; border-radius: 4px; }\
        #                    QWidget:focus { border: 2px solid white; border-radius: 4px; }")

        #FIXME: Is there are more elegant way to handle this?

        self.setMouseTracking(True)

        # invisible cursor to enable custom cursor
        self._hiddenCursor = QCursor(Qt.BlankCursor)
        # For screen recording BlankCursor doesn't work
        #self.hiddenCursor = QCursor(Qt.ArrowCursor)  
        
    def _cleanUp(self):        
        self._ticker.stop()
        del self._ticker

    def indicateSlicingPositionSettled(self, settled):
        self.scene().indicateSlicingPositionSettled(settled)

    def viewportRect(self):
        """
        Return a QRectF giving the part of the scene currently displayed in this
        widget's viewport in the scene's coordinates
        """
        return self.mapToScene(self.viewport().geometry()).boundingRect()
   
    def mapScene2Data(self, pos):
        return self.scene().scene2data.map(pos)
   
    # We have to overload some QGraphicsView event handlers with a nop to make the event switch work.
    # Otherwise, the events are not catched by our eventFilter.
    # There is no real reason for this behaviour: seems to be just a quirky qt implementation detail.
    def mouseMoveEvent(self, event):
        event.ignore()
    def mouseReleaseEvent(self, event):
        event.ignore()
    def mouseDoubleClickEvent( self, event):
        event.ignore()
    def wheelEvent(self, event):
        event.ignore()

    def _panning(self):
        hBar = self.horizontalScrollBar()
        vBar = self.verticalScrollBar()
        vBar.setValue(vBar.value() - self._deltaPan.y())
        if self.isRightToLeft():
            hBar.setValue(hBar.value() + self._deltaPan.x())
        else:
            hBar.setValue(hBar.value() - self._deltaPan.x())
        
    def _deaccelerate(self, speed, a=1, maxVal=64):
        x = self._qBound(-maxVal, speed.x(), maxVal)
        y = self._qBound(-maxVal, speed.y(), maxVal)
        ax ,ay = self._setdeaccelerateAxAy(speed.x(), speed.y(), a)
        if x > 0:
            x = max(0.0, x - a*ax)
        elif x < 0:
            x = min(0.0, x + a*ax)
        if y > 0:
            y = max(0.0, y - a*ay)
        elif y < 0:
            y = min(0.0, y + a*ay)
        return QPointF(x, y)

    def _qBound(self, minVal, current, maxVal):
        """PyQt4 does not wrap the qBound function from Qt's global namespace
           This is equivalent."""
        return max(min(current, maxVal), minVal)
    
    def _setdeaccelerateAxAy(self, x, y, a):
        x = abs(x)
        y = abs(y)
        if x > y:
            if y > 0:
                ax = int(x / y)
                if ax != 0:
                    return ax, 1
            else:
                return x/a, 1
        if y > x:
            if x > 0:
                ay = int(y/x)
                if ay != 0:
                    return 1, ay
            else:
                return 1, y/a
        return 1, 1

    def _tickerEvent(self):
        if self._deltaPan.x() == 0.0 and self._deltaPan.y() == 0.0 or self._dragMode == True:
            self._ticker.stop()
        else:
            self._deltaPan = self._deaccelerate(self._deltaPan)
            self._panning()

    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def fitImage(self):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        width, height = self.size().width() / self.sceneRect().width(), self.height() / self.sceneRect().height()
        self._zoomFactor = min(width, height)
                
    def centerImage(self):
        self.centerOn(self.sceneRect().width()/2 + self.sceneRect().x(), self.sceneRect().height()/2 + self.sceneRect().y()) 
    
    def toggleHud(self):
        if self._hud is not None:
            self._hud.setVisible(not self._hud.isVisible())

    def setHudVisible(self, visible):
        if self._hud is not None:
            self._hud.setVisible(visible)
    
    def focusInEvent(self, event):
        if self._hud is not None:
            self._hud.changeOpacity(1)
        self.focusChanged.emit()
        
    def focusOutEvent(self, event):
        if self._hud is not None:
            self._hud.changeOpacity(0.6)
     
    def changeViewPort(self,qRectf):
        self.fitInView(qRectf,mode = Qt.KeepAspectRatio)
        width, height = self.size().width() / qRectf.width(), self.height() / qRectf.height()
        self._zoomFactor = min(width, height)

    def doScale(self, factor):
        self._zoomFactor = self._zoomFactor * factor
        self.scale(factor, factor)
        
    def doScaleTo(self, zoom=1):
        factor = ( 1 / self._zoomFactor ) * zoom
        self._zoomFactor = zoom
        self.scale(factor, factor)
        

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************
if __name__ == '__main__':
    import sys
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QMainWindow
    from scipy.misc import lena
    
    def checkerboard(shape, squareSize):
        cb = numpy.zeros(shape)
        for i in range(shape[0]/squareSize):
            for j in range(shape[1]/squareSize):
                a = i*squareSize
                b = min((i+1)*squareSize, shape[0])
                c = j*squareSize
                d = min((j+1)*squareSize, shape[1])
                if i%2 == j%2:
                    cb[a:b,c:d] = 255
        return cb
    
    def cross(shape, width):
        c = numpy.zeros(shape)
        w2 = shape[0]/2
        h2 = shape[1]/2
        c[0:shape[0], h2-width/2:h2+width/2] = 255
        c[w2-width/2:w2+width/2, 0:shape[1]] = 255
        return c
    
    class ImageView2DTest(QMainWindow):    
        def __init__(self):
            assert False, "I'm broken. Please fixme."
            QMainWindow.__init__(self)
            
            self.lena = lena().swapaxes(0,1)
            self.checkerboard = checkerboard(self.lena.shape, 20)
            self.cross = cross(self.lena.shape, 30)

            self.imageView2D = ImageView2D()
            self.imageView2D.name = 'ImageView2D:'
            self.imageView2D.shape = self.lena.shape
            self.imageView2D.slices = 1
            self.setCentralWidget(self.imageView2D)

            #imageSlice = OverlaySlice(self.lena, color = QColor("red"), alpha = 1.0, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            #cbSlice    = OverlaySlice(self.checkerboard, color = QColor("green"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            #crossSlice = OverlaySlice(self.cross, color = QColor("blue"), alpha = 0.5, colorTable = None, min = None, max = None, autoAlphaChannel = False)
            
            self.imageView2D.scene().setContent(self.imageView2D.viewportRect(), None, (imageSlice, cbSlice, crossSlice))
         
    app = QApplication(sys.argv)
    i = ImageView2DTest()
    i.show()
    app.exec_()

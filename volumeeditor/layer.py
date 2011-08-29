from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QColor
from functools import partial

#*******************************************************************************
# L a y e r                                                                    *
#*******************************************************************************

class Layer( QObject ):
    '''
    Entries of a LayerStackModel,
    which is in turn displayed to the user via a LayerStackWidget
    
    properties:
    datasources -- list of ArraySourceABC; read-only
    visible -- boolean
    opacity -- float; range 0.0 - 1.0

    '''
    changed        = pyqtSignal()
    visibleChanged = pyqtSignal(bool)
    opacityChanged = pyqtSignal(float)
    nameChanged    = pyqtSignal(object)

    @property
    def visible( self ):
        return self._visible
    @visible.setter
    def visible( self, value ):
        if value != self._visible:
            self._visible = value
            self.visibleChanged.emit( value )
            self.changed.emit()

    @property
    def opacity( self ):
        return self._opacity
    @opacity.setter
    def opacity( self, value ):
        if value != self._opacity:
            self._opacity = value
            self.opacityChanged.emit( value )
            self.changed.emit()
            
    @property
    def name( self ):
        return self._name
    @name.setter
    def name( self, n ):
        if self._name != n:
            self._name = n
            self.nameChanged.emit(n)
            self.changed.emit()

    @property
    def datasources( self ):
        return self._datasources

    def contextMenu(self, parent, pos):
        print "no context menu implemented"

    def __init__( self, opacity = 1.0, visible = True ):
        super(Layer, self).__init__()
        self._name    = "Unnamed Layer"
        self.mode = "ReadOnly"
        self._visible = visible
        self._opacity = opacity


#*******************************************************************************
# G r a y s c a l e L a y e r                                                  *
#*******************************************************************************

class GrayscaleLayer( Layer ):
    thresholdingChanged = pyqtSignal(int, int)
    
    def __init__( self, datasource, thresholding = None ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]
        self._thresholding = thresholding
    @property
    def thresholding(self):
        """returns a tuple with the range [minimum value, maximum value]"""
        return self._thresholding
    @thresholding.setter
    def thresholding(self, t):
        self._thresholding = t
        self.thresholdingChanged.emit(t[0], t[1])
    
    def contextMenu(self, parent, pos):
        from widgets.layerDialog import GrayscaleLayerDialog
        from PyQt4.QtGui import QMenu, QAction
         
        menu = QMenu("Menu", parent)
        
        title = QAction("%s" % self.name, menu)
        title.setEnabled(False)
        menu.addAction(title)
        menu.addSeparator()
        
        adjThresholdAction = QAction("Adjust thresholds", menu)
        menu.addAction(adjThresholdAction)

        ret = menu.exec_(pos)
        if ret == adjThresholdAction:
            
            dlg = GrayscaleLayerDialog(parent)
            dlg.setLayername(self.name)
            def dbgPrint(a, b):
                self.thresholding = (a,b)
                print "range changed to [%d, %d]" % (a,b)
            dlg.grayChannelThresholdingWidget.rangeChanged.connect(dbgPrint)
            dlg.show()

#*******************************************************************************
# A l p h a M o d u l a t e d L a y e r                                        *
#*******************************************************************************

class AlphaModulatedLayer( Layer ):
    tintColorChanged = pyqtSignal(QColor)
    
    def __init__( self, datasource, tintColor = QColor(255,0,0), normalize = None ):
        super(AlphaModulatedLayer, self).__init__()
        self._datasources = [datasource]
        self._normalize = normalize
        self._tintColor = tintColor
    @property
    def tintColor(self):
        return self._tintColor
    @tintColor.setter
    def tintColor(self, c):
        if self._tintColor != c:
            self._tintColor = c
            self.tintColorChanged.emit(c)

#*******************************************************************************
# C o l o r t a b l e L a y e r                                                *
#*******************************************************************************

class ColortableLayer( Layer ):
    def __init__( self, datasource , colorTable):
        super(ColortableLayer, self).__init__()
        self._datasources = [datasource]
        self.colorTable = colorTable

#*******************************************************************************
# R G B A L a y e r                                                            *
#*******************************************************************************

class RGBALayer( Layer ):
    """
    signal thresholdingChanged:
    int -- index from 0 to 4 (RGBA)
    int -- lower threshold
    int -- upper threshold
    """
    thresholdingChanged = pyqtSignal(int, int, int)
    
    @property
    def color_missing_value( self ):
        return self._color_missing_value

    @property
    def alpha_missing_value( self ):
        return self._alpha_missing_value

    def __init__( self, red = None, green = None, blue = None, alpha = None, \
                  color_missing_value = 0, alpha_missing_value = 255,
                  normalizeR=None, normalizeG=None, normalizeB=None, normalizeA=None):
        super(RGBALayer, self).__init__()
        self._datasources = [red,green,blue,alpha]
        self._normalize   = [normalizeR, normalizeG, normalizeB, normalizeA]
        self._color_missing_value = color_missing_value
        self._alpha_missing_value = alpha_missing_value
        self._ranges = 4*[(0,255)]
    
    @property
    def rangeRed(self):
        return self._ranges[0]
    @rangeRed.setter
    def rangeRed(self, r):
        self._ranges[0] = r
        
    @property
    def rangeGreen(self):
        return self._ranges[1]
    @rangeGreen.setter
    def rangeGreen(self, r):
        self._ranges[1] = r
        
    @property
    def rangeBlue(self):
        return self._ranges[2]
    @rangeBlue.setter
    def rangeBlue(self, r):
        self._ranges[2] = r
        
    @property
    def rangeAlpha(self):
        return self._ranges[3]
    @rangeAlpha.setter
    def rangeAlpha(self, r):
        self._ranges[3] = r
    
    @property
    def thresholdingRed(self):
        return self._normalize[0]
    @thresholdingRed.setter
    def thresholdingRed(self, t):
        self._normalize[0] = t
        self.thresholdingChanged.emit(0, t[0], t[1])
        
    @property
    def thresholdingGreen(self):
        return self._normalize[1]
    @thresholdingGreen.setter
    def thresholdingGreen(self, t):
        self._normalize[1] = t
        self.thresholdingChanged.emit(1, t[0], t[1])
    
    @property
    def thresholdingBlue(self):
        return self._normalize[2]
    @thresholdingBlue.setter
    def thresholdingBlue(self, t):
        self._normalize[2] = t
        self.thresholdingChanged.emit(2, t[0], t[1])
    
    @property
    def thresholdingAlpha(self):
        return self._normalize[3]
    @thresholdingAlpha.setter
    def thresholdingAlpha(self, t):
        self._normalize[3] = t
        self.thresholdingChanged.emit(3, t[0], t[1])
    
    def setThresholding(self, channel, lower, upper):
        self._normalize[channel] = (lower, upper)
        self.thresholdingChanged.emit(channel, lower, upper)
            
    def contextMenu(self, parent, pos):
        from widgets.layerDialog import RGBALayerDialog
        from PyQt4.QtGui import QMenu, QAction
         
        menu = QMenu("Menu", parent)
        
        title = QAction("%s" % self.name, menu)
        title.setEnabled(False)
        menu.addAction(title)
        menu.addSeparator()
        
        adjThresholdAction = QAction("Adjust thresholds", menu)
        menu.addAction(adjThresholdAction)

        ret = menu.exec_(pos)
        if ret == adjThresholdAction:
            
            dlg = RGBALayerDialog(parent)
            dlg.setLayername(self.name)
            if self._datasources[0] == None:
                dlg.showRedThresholds(False)
            if self._datasources[1] == None:
                dlg.showGreenThresholds(False)
            if self._datasources[2] == None:
                dlg.showBlueThresholds(False)
            if self._datasources[3] == None:
                dlg.showAlphaThresholds(False)
             
            def dbgPrint(layer, a, b):
                self.setThresholding(layer, a, b)
                print "range changed for channel=%d to [%d, %d]" % (layer, a,b)
            dlg.redChannelThresholdingWidget.rangeChanged.connect(  partial(dbgPrint, 0))
            dlg.greenChannelThresholdingWidget.rangeChanged.connect(partial(dbgPrint, 1))
            dlg.blueChannelThresholdingWidget.rangeChanged.connect( partial(dbgPrint, 2))
            dlg.alphaChannelThresholdingWidget.rangeChanged.connect(partial(dbgPrint, 3))
            
            dlg.redChannelThresholdingWidget.setRange(self.rangeRed[0], self.rangeRed[1])
            dlg.greenChannelThresholdingWidget.setRange(self.rangeGreen[0], self.rangeGreen[1])
            dlg.blueChannelThresholdingWidget.setRange(self.rangeBlue[0], self.rangeBlue[1])
            dlg.alphaChannelThresholdingWidget.setRange(self.rangeAlpha[0], self.rangeAlpha[1])
            
            dlg.resize(dlg.minimumSize())
            dlg.show()

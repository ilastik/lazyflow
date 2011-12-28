from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QColor
from widgets.layerDialog import GrayscaleLayerDialog
from widgets.layerDialog import RGBALayerDialog


#*******************************************************************************
# L a y e r                                                                    *
#*******************************************************************************

class Layer( QObject ):
    '''
    properties:
    datasources -- list of ArraySourceABC; read-only
    visible -- boolean
    opacity -- float; range 0.0 - 1.0
    name -- string

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

    def __init__( self ):
        super(Layer, self).__init__()
        self._name = "Unnamed Layer"
        self._visible = True
        self._opacity = 1.0
        self._datasources = []



class NormalizableLayer( Layer ):
    """
    int -- datasource index
    int -- lower threshold
    int -- upper threshold
    """
    normalizeChanged = pyqtSignal(int, int, int)

    @property
    def range( self ):
        return self._range
    def set_range( self, datasourceIdx, value ):
        '''
        value -- (rmin, rmax)
        '''
        self._range[datasourceIdx] = value 
    
    @property
    def normalize( self ):
        return self._normalize
    def set_normalize( self, datasourceIdx, value ):
        '''
        value -- (nmin, nmax)
        '''
        self._normalize[datasourceIdx] = value 
        self.normalizeChanged.emit(datasourceIdx, value[0], value[1])

    def __init__( self ):
        super(NormalizableLayer, self).__init__()
        self._normalize = []
        self._range = []


#*******************************************************************************
# G r a y s c a l e L a y e r                                                  *
#*******************************************************************************

class GrayscaleLayer( NormalizableLayer ):
    def __init__( self, datasource, range = (0,255), normalize = (0,255) ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]
        self._normalize = [normalize]
        self._range = [range] 

#*******************************************************************************
# A l p h a M o d u l a t e d L a y e r                                        *
#*******************************************************************************

class AlphaModulatedLayer( NormalizableLayer ):
    @property
    def tintColor(self):
        return self._tintColor
    @tintColor.setter
    def tintColor(self, c):
        if self._tintColor != c:
            self._tintColor = c
            self.tintColorChanged.emit(c)
    
    def __init__( self, datasource, tintColor = QColor(255,0,0), range = (0,255), normalize = (0,255) ):
        super(AlphaModulatedLayer, self).__init__()
        self._datasources = [datasource]
        self._normalize = [normalize]
        self._range = [range]
        self._tintColor = tintColor



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

class RGBALayer( NormalizableLayer ):
    channelIdx = {'red': 0, 'green': 1, 'blue': 2, 'alpha': 3}
    channelName = {0: 'red', 1: 'green', 2: 'blue', 3: 'alpha'}
    
    @property
    def color_missing_value( self ):
        return self._color_missing_value

    @property
    def alpha_missing_value( self ):
        return self._alpha_missing_value

    def __init__( self, red = None, green = None, blue = None, alpha = None, \
                  color_missing_value = 0, alpha_missing_value = 255,
                  range = 4*[(0,255)],
                  normalizeR=(0,255), normalizeG=(0,255), normalizeB=(0,255), normalizeA=(0,255)):
        super(RGBALayer, self).__init__()
        self._datasources = [red,green,blue,alpha]
        self._normalize   = [normalizeR, normalizeG, normalizeB, normalizeA]
        self._color_missing_value = color_missing_value
        self._alpha_missing_value = alpha_missing_value
        self._range = range

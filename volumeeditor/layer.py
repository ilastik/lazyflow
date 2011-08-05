from PyQt4.QtCore import QObject, pyqtSignal

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
    visibleChanged = pyqtSignal(bool)
    opacityChanged = pyqtSignal(float)

    @property
    def visible( self ):
        return self._visible
    @visible.setter
    def visible( self, value ):
        if value != self._visible:
            self._visible = value
            self.visibleChanged.emit( value )

    @property
    def opacity( self ):
        return self._opacity
    @opacity.setter
    def opacity( self, value ):
        if value != self._opacity:
            self._opacity = value
            self.opacityChanged.emit( value )

    @property
    def datasources( self ):
        return self._datasources

    def __init__( self, opacity = 1.0, visible = True ):
        super(Layer, self).__init__()
        self.name    = "Unnamed Layer"
        self.mode = "ReadOnly"
        self._visible = visible
        self._opacity = opacity



#*******************************************************************************
# G r a y s c a l e L a y e r                                                  *
#*******************************************************************************

class GrayscaleLayer( Layer ):
    def __init__( self, datasource, normalize = (0.0,255.0) ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]
        self._normalize = normalize


#*******************************************************************************
# C o l o r t a b l e L a y e r                                                  *
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
    @property
    def color_missing_value( self ):
        return self._color_missing_value

    @property
    def alpha_missing_value( self ):
        return self._alpha_missing_value

    def __init__( self, red = None, green = None, blue = None, alpha = None, \
                  color_missing_value = 0, alpha_missing_value = 255):
        super(RGBALayer, self).__init__()
        self._datasources = [red,green,blue,alpha]
        self._color_missing_value = color_missing_value
        self._alpha_missing_value = alpha_missing_value

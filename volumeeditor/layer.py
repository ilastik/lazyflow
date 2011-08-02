from PyQt4.QtCore import QObject, pyqtSignal

class Layer( QObject ):
    '''Represents the visual properties and the associated raw data of a n-dimensional layer.

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
        self._visible = value
        self.visibleChanged.emit( value )

    @property
    def opacity( self ):
        return self._opacity
    @opacity.setter
    def opacity( self, value ):
        self._opacity = value
        self.opacityChanged.emit( value )


    @property
    def datasources( self ):
        return self._datasources

    def __init__( self, opacity = 1.0, visible = True ):
        self._visible = visible
        self._opacity = opacity

        self._datasources = []



class GrayscaleLayer( Layer ):
    def __init__( self, datasource ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]



class RGBALayer( Layer ):
    @property
    def color_missing_value( self ):
        return self._color_missing_value

    @property
    def alpha_missing_value( self ):
        return self._alpha_missing_value

    def __init__( self, red = None, green = None, blue = None, alpha = None, color_missing_value = 0, alpha_missing_value = 255):
        super(RGBALayer, self).__init__()
        self._datasources = [red,green,blue,alpha]
        self._color_missing_value = color_missing_value
        self._alpha_missing_value = alpha_missing_value


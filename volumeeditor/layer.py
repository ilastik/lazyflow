#*******************************************************************************
# L a y e r                                                                    *
#*******************************************************************************

class Layer( object ):
    """
    Entries of a LayerStackModel,
    which is in turn displayed to the user via a LayerStackWidget
    
    properties:
    datasources -- list of ArraySourceABC; read-only
    visible     -- boolean
    opacity      -- float; range 0.0 - 1.0
    """

    @property
    def datasources( self ):
        return self._datasources

    def __init__(self):
        self.mode = 'ReadOnly' #drawing related...
    
        self.name    = "Unnamed Layer"
        self.visible = True
        self.opacity = 1.0
        self._datasources = []

#*******************************************************************************
# G r a y s c a l e L a y e r                                                  *
#*******************************************************************************

class GrayscaleLayer( Layer ):
    def __init__( self, datasource ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]

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

from pixelpipeline.imagesources import GrayscaleImageSource, RGBAImageSource

class Layer( object ):
    def __init__( self ):
        self.visible = True
        self.opacity = 1.0

class GrayscaleLayer( Layer ):
    def __init__( self, datasource ):
        super(GrayscaleLayer, self).__init__()
        self.datasources = [datasource]

class RGBALayer( Layer ):
    def __init__( self, red = None, green = None, blue = None, alpha = None):
        super(RGBALayer, self).__init__()
        self.datasources = [red,green,blue,alpha]

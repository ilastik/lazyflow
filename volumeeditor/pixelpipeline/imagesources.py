from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QImage
from qimage2ndarray import gray2qimage

class MonochromeImageSource( QObject ):
    changed = pyqtSignal()
    
    @property
    def rect( self ):
        return self._rect
    @rect.setter
    def rect( self, rect ):
        self._rect = rect
        self.changed.emit()

    def __init__( self, sliceSource, rect = (0,0,128,128)):
        super(MonochromeImageSource, self).__init__()
        self._sliceSource = sliceSource
        self._rect = rect

    def request( self ):
        s = self._sliceSource.request()
        s = s[self.rect[0]: self.rect[0] + self.rect[2], self.rect[1]:self.rect[1] + self.rect[3]]
        img = gray2qimage(s)
        return img.convertToFormat(QImage.Format_ARGB32_Premultiplied)

'''
class AlphaModulatedImageSource( QObject ):
    changed = pyqtSignal()
    
    @property
    def rect( self ):
        return self._rect
    @rect.setter
    def rect( self, rect ):
        self._rect = rect

    def __init__( self, sliceSource, rect = (0,0,256,128)):
        super(ImageSource, self).__init__()
        self.sliceSource = sliceSource
        self._rect = rect

    def request( self ):
        pass
'''

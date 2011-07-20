from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QImage
from qimage2ndarray import gray2qimage
import asyncabcs

class GrayscaleImageRequest( object ):
    def __init__( self, arrayrequest ):
        self._arrayreq = arrayrequest

    def wait( self ):
        a = self._arrayreq.wait()
        img = gray2qimage(a)
        return img.convertToFormat(QImage.Format_ARGB32_Premultiplied)        
    def notify( self, callback, **kwargs ):
        self._arrayreq.notify(self._onNotify, package = (callback, kwargs))

    def _onNotify( self, result, package ):
        img = self.wait()
        callback = package[0]
        kwargs = package[1]
        callback( img, **kwargs )
asyncabcs.RequestABC.register(GrayscaleImageRequest)
assert issubclass(GrayscaleImageRequest, asyncabcs.RequestABC)


class GrayscaleImageSource( QObject ):
    def __init__( self, sliceSource ):
        assert isinstance(sliceSource, asyncabcs.ArraySourceABC)
        super(GrayscaleImageSource, self).__init__()
        self._sliceSource = sliceSource

    def request( self, rect ):
        req = self._sliceSource.request((slice(rect[0], rect[0] + rect[2]), slice(rect[1], rect[1] + rect[3])))
        return GrayscaleImageRequest( req )
asyncabcs.ImageSourceABC.register(GrayscaleImageSource)
assert issubclass(GrayscaleImageSource, asyncabcs.ImageSourceABC)



import unittest as ut
class GrayscaleImageSourceTest( ut.TestCase ):
    def testRequest( self ):
        from scipy.misc import lena
        from datasources import ArraySource
        raw = lena()
        a = ArraySource(raw)
        ims = GrayscaleImageSource( a )
        imr = ims.request((0,0,512,512))

        def check(result, codon):
            self.assertEqual(codon, "unique")
            self.assertTrue(type(result) == QImage)
        imr.notify(check, codon="unique")

if __name__ == '__main__':
    ut.main()

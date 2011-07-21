from PyQt4.QtCore import QObject, QRect, pyqtSignal
from PyQt4.QtGui import QImage
from qimage2ndarray import gray2qimage
import asyncabcs

class GrayscaleImageRequest( object ):
    def __init__( self, arrayrequest ):
        self._arrayreq = arrayrequest

    def wait( self ):
        a = self._arrayreq.wait()
        a = a.squeeze()
        img = gray2qimage(a)
        return img.convertToFormat(QImage.Format_ARGB32_Premultiplied)        
    def notify( self, callback, **kwargs ):
        self._arrayreq.notify(self._onNotify, package = (callback, kwargs))

    def _onNotify( self, result, package ):
        img = self.wait()
        callback = package[0]
        kwargs = package[1]
        callback( img, **kwargs )
assert issubclass(GrayscaleImageRequest, asyncabcs.RequestABC)


class GrayscaleImageSource( QObject ):
    changed = pyqtSignal(QRect)

    def __init__( self, sliceSource ):
        assert isinstance(sliceSource, asyncabcs.ArraySourceABC)
        super(GrayscaleImageSource, self).__init__()
        self._sliceSource = sliceSource
        self._sliceSource.throughChanged.connect(self._onThroughChanged)

    def request( self, qrect ):
        assert isinstance(qrect, QRect)
        s = (slice(qrect.y(), qrect.y()+qrect.height()), slice(qrect.x(), qrect.x()+qrect.width()))
        #s = (slice(qrect.x(), qrect.x()+qrect.width()), slice(qrect.y(), qrect.y()+qrect.height())) 
        print "LOOKLOOK GrayscaleImageSource", s
        req = self._sliceSource.request(s)
        return GrayscaleImageRequest( req )

    def _onThroughChanged( self, through):
        print "GrayScaleImageSource dirties everything"
        self.changed.emit(QRect())
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

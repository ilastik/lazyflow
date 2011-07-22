from PyQt4.QtCore import QObject, QRect, pyqtSignal
from PyQt4.QtGui import QImage
from qimage2ndarray import gray2qimage
import asyncabcs
from datasources import is_pure_slicing

def _is_bounded( slicing2d ):
    if slicing2d[0].stop == None:
        return False
    if slicing2d[1].stop == None:
        return False
    return True

def _slicing2rect( slicing2d ):
    x = slicing2d[1].start
    y = slicing2d[0].start
    width = slicing2d[1].stop - slicing2d[1].start
    height = slicing2d[0].stop - slicing2d[0].start
    return QRect(x, y, width, height)

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
    isDirty = pyqtSignal( QRect )

    def __init__( self, arraySource2D ):
        assert isinstance(arraySource2D, asyncabcs.ArraySourceABC)
        super(GrayscaleImageSource, self).__init__()
        self._arraySource2D = arraySource2D
        self._arraySource2D.isDirty.connect(self.setDirty)

    def request( self, qrect ):
        assert isinstance(qrect, QRect)
        s = (slice(qrect.y(), qrect.y()+qrect.height()), slice(qrect.x(), qrect.x()+qrect.width()))
        req = self._arraySource2D.request(s)
        return GrayscaleImageRequest( req )

    def setDirty( self, slicing ):
        if not is_pure_slicing(slicing):
            raise Exception('dirty region: slicing is not pure')
        if not _is_bounded( slicing ):
            self.isDirty.emit(QRect()) # empty rect == everything is dirty
        else:
            self.isDirty.emit(_slicing2rect( slicing ))
assert issubclass(GrayscaleImageSource, asyncabcs.ImageSourceABC)





import unittest as ut
class GrayscaleImageSourceTest( ut.TestCase ):
    def setUp( self ):
        from scipy.misc import lena
        from datasources import ArraySource
        self.raw = lena()
        self.ars = ArraySource(self.raw)
        self.ims = GrayscaleImageSource( self.ars )
        

    def testRequest( self ):
        imr = self.ims.request(QRect(0,0,512,512))
        def check(result, codon):
            self.assertEqual(codon, "unique")
            self.assertTrue(type(result) == QImage)
        imr.notify(check, codon="unique")

    def testSetDirty( self ):
        def checkAllDirty( rect ):
            self.assertTrue( rect.isEmpty() )

        def checkDirtyRect( rect ):
            self.assertEqual( rect.x(), 12 )
            self.assertEqual( rect.y(), 34 )
            self.assertEqual( rect.width(), 22 )
            self.assertEqual( rect.height(), 3  )

        # should mark everything dirty
        self.ims.isDirty.connect( checkAllDirty )
        self.ims.setDirty((slice(34,None), slice(12,34)))
        self.ims.isDirty.disconnect( checkAllDirty )

        # dirty subrect
        self.ims.isDirty.connect( checkDirtyRect )
        self.ims.setDirty((slice(34,37), slice(12,34)))
        self.ims.isDirty.disconnect( checkDirtyRect )

if __name__ == '__main__':
    ut.main()

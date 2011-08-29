import unittest as ut

from PyQt4.QtCore import QRect
from PyQt4.QtGui import QImage

from volumeeditor.pixelpipeline.imagesources import GrayscaleImageSource, RGBAImageSource

#*******************************************************************************
# G r a y s c a l e I m a g e S o u r c e T e s t                              *
#*******************************************************************************

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

#*******************************************************************************
# R G B A I m a g e S o u r c e T e s t                                        *
#*******************************************************************************

class RGBAImageSourceTest( ut.TestCase ):
    def setUp( self ):
        import numpy as np
        import os.path
        from datasources import ArraySource        
        from volumeeditor import _testing
        basedir = os.path.dirname(_testing.__file__)
        self.data = np.load(os.path.join(basedir, 'rgba129x104.npy'))
        self.red = ArraySource(self.data[:,:,0])
        self.green = ArraySource(self.data[:,:,1])
        self.blue = ArraySource(self.data[:,:,2])
        self.alpha = ArraySource(self.data[:,:,3])

        self.ims_rgba = RGBAImageSource( self.red, self.green, self.blue, self.alpha )
        self.ims_rgb = RGBAImageSource( self.red, self.green, self.blue )
        self.ims_rg = RGBAImageSource( self.red, self.green )
        self.ims_ba = RGBAImageSource( blue = self.blue, alpha = self.alpha )
        self.ims_a = RGBAImageSource( alpha = self.alpha )
        self.ims_none = RGBAImageSource()
        
    def testRgba( self ):
        img = self.ims_rgba.request(QRect(0,0,129,104)).wait()
        #img.save('rgba.tif')

    def testRgb( self ):
        img = self.ims_rgb.request(QRect(0,0,129,104)).wait()
        #img.save('rgb.tif')

    def testRg( self ):
        img = self.ims_rg.request(QRect(0,0,129,104)).wait()
        #img.save('rg.tif')

    def testBa( self ):
        img = self.ims_ba.request(QRect(0,0,129,104)).wait()
        #img.save('ba.tif')

    def testA( self ):
        img = self.ims_a.request(QRect(0,0,129,104)).wait()
        #img.save('a.tif')

    def testNone( self ):
        img = self.ims_none.request(QRect(0,0,129,104)).wait()
        #img.save('none.tif')

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == '__main__':
    ut.main()

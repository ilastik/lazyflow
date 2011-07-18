from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy.misc import lena
from pixelpipeline.datasources import *
from pixelpipeline.slicesources import *
from pixelpipeline.imagesources import *


class FakeImageView( QLabel ):
    def __init__( self, imageSource ):
        super(FakeImageView, self).__init__()
        self._imageSource = imageSource
        self.updateImage()

    def updateImage( self ):
        img = self._imageSource.request()
        pixmap = QPixmap()
        pixmap.convertFromImage(img)
        self.setPixmap(pixmap)
        print "image updated"
    


if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication([])
    label = QLabel()

    import numpy as np
    l1 = lena()
    l2 = l1.swapaxes(0,1)
    raw = np.zeros((1,512,512,2,1))
    raw[0,:,:,0,0] = l1
    raw[0,:,:,1,0] = l2
    dataSrc = DataSource(raw)

    sliceSrc = SpatialSliceSource5D(dataSrc)
    imageSrc = MonochromeImageSource(sliceSrc)

    view = FakeImageView(imageSrc)
    view.show()

    dataSrc.changed.connect(sliceSrc.changed.emit)
    sliceSrc.changed.connect(imageSrc.changed.emit)
    imageSrc.changed.connect(view.updateImage)

    import time
    def toggle():
        c = int((time.time()*50) % 256)
        print c
        dataSrc[0,100:200,30:200,0,0] = c
    def toggle2():
        r = list(imageSrc.rect)
        r[0] = int(np.random.rand()*128)
        r[1] = int(np.random.rand()*128)
        r[2] = int(np.random.rand()*500)
        r[3] = int(np.random.rand()*500)
        imageSrc.rect = r

    def toggle3():
        if sliceSrc.through == 1:
            sliceSrc.through = 0
        else:
            sliceSrc.through = 1


    timer = QTimer()
    timer.timeout.connect(toggle)
    timer.start(200)

    t2 = QTimer()
    t2.timeout.connect(toggle2)
    t2.start(1000)

    t3 = QTimer()
    t3.timeout.connect(toggle3)
    t3.start(1500)

    app.exec_()

    


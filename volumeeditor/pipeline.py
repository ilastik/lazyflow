from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy.misc import lena
from qimage2ndarray import *

class Source( QObject ):
    changed = pyqtSignal()

    def onOriginChanged( self ):
        self.changed.emit()
    
    def request( self ):
        raise NotImplementedError()



class DataSource( QObject ):
    changed = pyqtSignal()

    def __init__( self, data ):
        super(DataSource, self).__init__()
        self._data = data

    def onOriginChanged( self ):
        self.changed.emit()
    
    def __getitem__( self, slicing):
        return self._data[slicing]

    def __setitem__( self, slicing, value ):
        self._data[slicing] = value
        self.changed.emit()


def mkSlicer( abscissa = 1, ordinate = 2, along = [0,3,4] ):
    assert(hasattr(along, "__iter__"))
    def slicer( array, through = [0,0,0], rect = ((None, None), (None,None)) ):
        slicing = range(len(through) + 2)
        slicing[abscissa] = slice(rect[0][0], rect[1][0])
        slicing[ordinate] = slice(rect[0][1], rect[1][1])
        for i,a in enumerate(along):
            slicing[a] = through[i]
        return array[slicing]
    return slicer

class SpatialSliceSource( QObject ):
    changed = pyqtSignal()

    @property
    def sliceNo( self ):
        return self._sliceNo
    @sliceNo.setter
    def sliceNo( self, value ):
        self._sliceNo = value
        self.changed.emit()

    def __init__( self, dataSource, along = 'z' ):
        super(SliceSource, self).__init__()
        self.time = 0
        self.channel = 0

        self._along = along
        self._dataSource = dataSource
        self._sliceNo = 0

        self._slicer = mkSlicer(1,2,[0,3,4])

    def request( self ):
        return self._slicer(self._dataSource, [self.time, self.sliceNo, self.channel])

class MonochromeImageSource( QObject ):
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
        s = self.sliceSource.request()
        s = s[self.rect[0]: self.rect[0] + self.rect[2], self.rect[1]:self.rect[1] + self.rect[3]]
        img = gray2qimage(s)
        return img.convertToFormat(QImage.Format_ARGB32_Premultiplied)

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
    raw = np.zeros((512,512,2))
    raw[:,:,0] = l1
    raw[:,:,1] = l2
    dataSrc = DataSource(raw)

    sliceSrc = SliceSource(dataSrc)
    imageSrc = ImageSource(sliceSrc)

    view = FakeImageView(imageSrc)
    view.show()

    dataSrc.changed.connect(sliceSrc.changed.emit)
    sliceSrc.changed.connect(imageSrc.changed.emit)
    imageSrc.changed.connect(view.updateImage)

    import time
    def toggle():
        #if sliceSrc.sliceNo == 1:
        #    sliceSrc.sliceNo = 0
        #else:
        #    sliceSrc.sliceNo = 1
        c = int((time.time()*50) % 256)
        print c
        dataSrc[100:200,30:200,0] = c
    def toggle2():
        r = list(imageSrc.rect)
        r[0] = int(np.random.rand()*128)
        r[1] = int(np.random.rand()*128)
        r[2] = int(np.random.rand()*500)
        r[3] = int(np.random.rand()*500)

        imageSrc.rect = r

    timer = QTimer()
    timer.timeout.connect(toggle)
    timer.start(200)

    t2 = QTimer()
    t2.timeout.connect(toggle2)
    t2.start(1000)


    app.exec_()

    


from PyQt4.QtCore import QThread, pyqtSignal, QPoint, QSize, Qt
from PyQt4.QtGui import QPainter, QColor, QImage

import numpy, qimage2ndarray
import threading
from collections import deque

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************

class ImageSceneRenderThread(QThread):
    finishedQueue = pyqtSignal()
    patchAvailable = pyqtSignal(int)
    
    def __init__(self, imagePatches, imageSource, parent = None):
        QThread.__init__(self, parent)
        self._imagePatches = imagePatches

        self._queue = deque()
        
        self._dataPending = threading.Event()
        self._dataPending.clear()
        self._stopped = False
        
        # experimental
        self._imageSource = imageSource

    def requestPatch(self, patchNr):
        if patchNr not in self._queue:
            self._queue.append(patchNr)
            self._dataPending.set()

    def stop(self):
        self._stopped = True
        self._dataPending.set()
        self.wait()

    # private functions

    def _callMyFunction(self, itemdata, origitem, origitemColor, itemcolorTable):
        uint8image = _convertImageUInt8(itemdata, itemcolorTable)

        if itemcolorTable != None and _isRGB(uint8image):
            return qimage2ndarray.array2qimage(uint8image.swapaxes(0,1), normalize=False)
        if itemcolorTable != None:
            image0 = qimage2ndarray.gray2qimage(uint8image.swapaxes(0,1), normalize=False)
            image0.setColorTable(itemcolorTable[:])
            return image0
            
        if origitem.min is not None and origitem.max is not None:
            normalize = (origitem.min, origitem.max)
        else:
            normalize = False
                                        
        if origitem.autoAlphaChannel is False and _isRGB(itemdata):
            return qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
        if origitem.autoAlphaChannel is False:
            tempdat = numpy.zeros(itemdata.shape[0:2] + (3,), 'float32')
            tempdat[:,:,0] = origitemColor.redF()*itemdata[:]
            tempdat[:,:,1] = origitemColor.greenF()*itemdata[:]
            tempdat[:,:,2] = origitemColor.blueF()*itemdata[:]
            return qimage2ndarray.array2qimage(tempdat.swapaxes(0,1), normalize)
        else: #autoAlphaChannel == True
            image1 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
            image0 = QImage(itemdata.shape[0],itemdata.shape[1],QImage.Format_ARGB32)
            image0.fill(origitemColor.rgba())
            image0.setAlphaChannel(image1)
            return image0

    def _takeJob(self):
        patchNr = self._queue.pop()
        
        patch = self._imagePatches[patchNr]
        patch.rendering = True
        '''
        p = QPainter(patch.image)
        r = patch.rectF

        #add overlays
        for index, origitem in enumerate(overlays):
            # before the first layer is painted, initialize it white to enable sound alpha blending
            if index == 0:
                p.fillRect(0,0,r.width(), r.height(), Qt.white)
            
            p.setOpacity(origitem.alpha)
            itemcolorTable = origitem.colorTable
            
            imagedata = origitem._data[r.left():r.right()+1,r.top():r.bottom()+1]
            image0 = self.callMyFunction(imagedata, origitem, _asQColor(origitem.color), itemcolorTable)

            p.drawImage(0,0, image0)
        p.end()
        '''
        img = self._imageSource.request(patch.rect).wait()
        patch.image = img
        patch.dirty = False
        patch.rendering = False
        self.patchAvailable.emit(patchNr)

    def _runImpl(self):
        self._dataPending.wait()
        while len(self._queue) > 0:
            self._takeJob()
        self._dataPending.clear()
    
    def run(self):
        while not self._stopped:
            self._runImpl()

def _convertImageUInt8(itemdata, itemcolorTable):
    if itemdata.dtype == numpy.uint8 or itemcolorTable == None:
        return itemdata
    if itemcolorTable is None and itemdata.dtype == numpy.uint16:
        print '*** Normalizing your data for display purpose'
        print '*** I assume you have 12bit data'
        return (itemdata*255.0/4095.0).astype(numpy.uint8)
    
    #if the item is larger we take the values module 256
    #since QImage supports only 8Bit Indexed images
    olditemdata = itemdata              
    itemdata = numpy.ndarray(olditemdata.shape, 'float32')
    if olditemdata.dtype == numpy.uint32:
        return numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
    elif olditemdata.dtype == numpy.uint64:
        return numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
    elif olditemdata.dtype == numpy.int32:
        return numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
    elif olditemdata.dtype == numpy.int64:
        return numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
    elif olditemdata.dtype == numpy.uint16:

        return numpy.right_shift(numpy.left_shift(olditemdata,8),8)[:]
    #raise TypeError(str(olditemdata.dtype) + ' <- unsupported image _data type (in the rendering thread, you know) ')
    # TODO: Workaround: tried to fix the problem
    # with the segmentation display, somehow it arrieves
    # here in float32
    print TypeError(str(olditemdata.dtype) + ': unsupported dtype of overlay in ImageSceneRenderThread.run()')

def _isRGB( image ):
    return len(image.shape) > 2 and image.shape[2] > 1

def _asQColor( color ):
    if isinstance(color,  long) or isinstance(color,  int):
        return QColor.fromRgba(long(color))
    return color


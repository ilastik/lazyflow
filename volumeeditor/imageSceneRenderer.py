from PyQt4.QtCore import QObject, QThread, pyqtSignal, QRectF
from PyQt4.QtGui import QPainter, QColor, QImage

import numpy, qimage2ndarray
import threading
from collections import deque

try:
    from OpenGL.GL import *
except Exception, e:
    print e
    pass

#*******************************************************************************
# I m a g e S c e n e R e n d e r e r                                          *
#*******************************************************************************

# check minimal version of the opengl python wrapper
#
# to avoid copies, we want to call glTexImage2D(..., pixels)
# with 'pixels' of type ctypes.c_void_p. This is not supported
# in older versions of the wrapper code
from distutils.version import LooseVersion 
if LooseVersion(OpenGL.__version__) < LooseVersion('3.0.1'):
    raise Exception('PyOpenGL version is less than 3.0.1')

class ImageSceneRenderer(QObject):
    updatesAvailable = pyqtSignal() 
    
    def __init__(self, patchAccessor, imagePatches, glWidget = None):
        QObject.__init__(self)
        self._patchAccessor = patchAccessor
        self._glWidget = glWidget
        self._imagePatches = imagePatches

        self._min = 0
        self._max = 255
        
        self._thread = ImageSceneRenderThread(patchAccessor, imagePatches)
        self._thread.finishedQueue.connect(self._renderingThreadFinished)
        self._thread.start()

    def renderImage(self, rect, image, overlays = ()):
        #Abandon previous workloads
        self._thread.queue.clear()
        self._thread.newerDataPending.set()
        #Find all patches that intersect the given 'rect'.
        from time import time
        tic = time()
        patches = []
        for i in range(self._patchAccessor.patchCount):
            r = self._patchAccessor.patchRectF(i)
            if rect.intersects(r):
                patches.append(i)
        if len(patches) == 0: return
        toc = time()
        print toc-tic
        #Update these patches using the thread below
        print "ImageSceneRenderer.renderImage: render %d tiles of %d" % (len(patches), self._patchAccessor.patchCount)
        workPackage = [patches, image, overlays, self._min, self._max]
        self._thread.queue.append(workPackage)
        self._thread.dataPending.set()

    def _updateTexture(self, patch, b):
        glTexSubImage2D(GL_TEXTURE_2D, 0, b[0], b[2], b[1]-b[0], b[3]-b[2], \
                        GL_RGB, GL_UNSIGNED_BYTE, \
                        ctypes.c_void_p(patch.bits().__int__()))
    
    def _renderingThreadFinished(self):
        def haveNewData():
            return self._thread.dataPending.isSet()
        
        #only proceed if there is no new _data already in the rendering thread queue
        if not haveNewData():
            #if we are in opengl 2d render mode, update the texture

#            if self._glWidget:
#                self._glWidget.context().makeCurrent()
#                glBindTexture(GL_TEXTURE_2D, self._glTexture)
#                for patchNr in self._thread.outQueue:
#                    if haveNewData(): break
#                    b = self._imageScene.patchAccessor.getPatchBounds(patchNr, 0)
#                    self._updateTexture(self._imagePatches[patchNr], b)
                    
            self._thread.outQueue.clear()

#FIXME
#if all updates have been rendered remove tempitems
#            if self._thread.queue.__len__() == 0:
#                for item in self._imageScene.tempImageItems:
#                    self._imageScene.scene().removeItem(item)
#                self._imageScene.tempImageItems = []
 
        if not haveNewData():
            self.updatesAvailable.emit()
        
        self._thread.freeQueue.set()

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************

class ImageSceneRenderThread(QThread):
    finishedQueue = pyqtSignal()
    
    def __init__(self, patchAccessor, imagePatches):
        QThread.__init__(self, None)
        self._patchAccessor = patchAccessor
        self._imagePatches  = imagePatches

        self.queue = deque(maxlen=1)
        self.outQueue = deque()
        self.dataPending = threading.Event()
        self.dataPending.clear()
        self.newerDataPending = threading.Event()
        self.newerDataPending.clear()
        self.freeQueue = threading.Event()
        self.freeQueue.clear()
        self.stopped = False
        
        print "initialized ImageSceneRenderThread"

    def callMyFunction(self, itemdata, origitem, origitemColor, itemcolorTable):
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
            print itemdata.shape
            image1 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
            image0 = QImage(itemdata.shape[0],itemdata.shape[1],QImage.Format_ARGB32)
            image0.fill(origitemColor.rgba())
            image0.setAlphaChannel(image1)
            return image0

    def takeJob(self):
        workPackage = self.queue.pop()
        if workPackage is None:
            return
        patchNumbers, origimage, overlays, min, max = workPackage
        for patchNr in patchNumbers:
            if self.newerDataPending.isSet():
                self.newerDataPending.clear()
                break
            bounds = self._patchAccessor.getPatchBounds(patchNr)

            imagePatch = self._imagePatches[patchNr]
            p = QPainter(imagePatch)

            #add overlays
            for index, origitem in enumerate(overlays):
                if index == 0 and origitem.alpha < 1.0:
                    p.eraseRect(QPoint(0,0),bounds[1]-bounds[0],bounds[3]-bounds[2])
                
                p.setOpacity(origitem.alpha)
                itemcolorTable = origitem.colorTable
                
                imagedata = origitem._data[bounds[0]:bounds[1],bounds[2]:bounds[3]]
                image0 = self.callMyFunction(imagedata, origitem, _asQColor(origitem.color), itemcolorTable)

                p.drawImage(0,0, image0)
            p.end()
            
            self.outQueue.append(patchNr)

    def _runImpl(self):
        self.finishedQueue.emit()
        self.dataPending.wait()
        self.newerDataPending.clear()
        self.freeQueue.clear()
        while len(self.queue) > 0:
            self.takeJob()
        self.dataPending.clear()
    
    def run(self):
        while not self.stopped:
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


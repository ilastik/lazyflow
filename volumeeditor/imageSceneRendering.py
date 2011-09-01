from PyQt4.QtCore import QThread, pyqtSignal, Qt, QMutex
from PyQt4.QtGui import QPainter

import threading
from collections import deque

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************

class Requests(object):
    def __init__(self):
        self._mutex = QMutex()
        self._id2r = dict()
        self._r = set()

    def addRequest(self, reqId, request):
        self._mutex.lock()
        
        if not reqId in self._id2r:
            self._id2r[reqId] = []
        self._id2r[reqId].append(request)
        self._r.add(request)
        
        self._mutex.unlock()
        
    def removeById(self, reqId):
        self._mutex.lock()
        if id in self._id2r:
            for req in self._id2r[reqId]:
                self._r.remove(req)
                req.cancel()
            del self._id2r[reqId]
        self._mutex.unlock()
    
    def cancelAll(self):
        self._mutex.lock()
        
        for r in self._r:
            r.cancel()
        self._r = set()
        self._id2r = dict()
        self._mutex.unlock()

    def removeByRequest(self, req):
        self._mutex.lock()
        if req in self._r:
            reqId = (reqId for reqId, r in self._id2r.items() if req in r).next()
            self._id2r[reqId].remove(req)
            self._r.remove(req)
            req.cancel()
        self._mutex.unlock()

class ImageSceneRenderThread(QThread):
    """
    Composites individual patches. For one patch,
    it requests the corresponding region for all the
    visible layers in the layer stack as QImage objects,
    and then uses alpha blending to arrive at a final
    output image.
    As alpha blending of RGBA pre-multiplied images is an associative
    operation, the order of the incoming patches (which have an
    associated layer) does not matter.
    
    A particular patch can be requested via `requestPatch`
    A signal is emitted on completion of a request `patchAvailable`
    """
    
    patchAvailable = pyqtSignal(int)
    
    def __init__(self, stackedImageSources, parent=None):
        #assert hasattr(stackedImageSources, '__iter__')
        QThread.__init__(self, parent)
        self._imagePatches = None

        self._queue = deque()
        
        self._dataPending = threading.Event()
        self._dataPending.clear()
        self._stopped = False

        self._stackedIms = stackedImageSources
        self._runningRequests = Requests()

    def requestPatch(self, patchNr):
        self._runningRequests.removeById(patchNr)
        
        if patchNr not in self._queue:
            self._queue.append(patchNr)
            self._dataPending.set()

    def stop(self):
        self.cancelAll()
        self._stopped = True
        self._dataPending.set()
        self.wait()
        
    def start(self):
        self._stopped = False
        QThread.start(self)

    def cancelAll(self):
        self._dataPending.clear()
        self._queue = deque()
        self._runningRequests.cancelAll()

    def _onPatchFinished(self, image, request, patchNumber, patchLayer):
        #
        # FIXME
        #
        # Currently, the asynchronous notify callback can interrupt the execution
        # of this thread at anytime. The request to the graph was issued from the
        # _takeJob function, which executes in the context of the render thread.
        # When the notify calls the _onPatchFinished, the callback will execute
        # in the same thread.
        #
        # We need to be very careful here
        # _no_ function executing in the context of the render thread is allowed to
        # use the cancelLock(), except this function
        #
        
        #acquire lock for 'cancel' operation
        request.cancelLock()
        #we might have been canceled!
        if request.canceled():
            return
        #no one will cancel this request before we release the lock...
        
        thisPatch = self._imagePatches[patchLayer][patchNumber]
        
        ### one layer of this patch is done, just assign the newly arrived image
        thisPatch.image = image
        ### ...done
        
        numLayers = len(self._imagePatches) - 2
        compositePatch = self._imagePatches[numLayers][patchNumber]
    
        ### render the composite patch ######             
        compositePatch.lock()
        compositePatch.dirty = True
        p = QPainter(compositePatch.image)
        r = compositePatch.imageRectF
        p.fillRect(0, 0, round(r.width()), round(r.height()), Qt.white)

        for layerNr in range(numLayers-1, -1, -1):
            if not self._stackedIms[layerNr].visible:
                continue
            patch = self._imagePatches[layerNr][patchNumber]
            p.setOpacity(self._stackedIms[layerNr].opacity)
            p.drawImage(0, 0, patch.image)
        p.end()
        compositePatch.imgVer = compositePatch.reqVer
        
        compositePatch.unlock()
        ### ...done rendering ################
        
        self.patchAvailable.emit(patchNumber)
        
        request.cancelUnlock()
        
        #Now that the lock has been released, we can remove the (done)
        #request (which will lock the request again)
        self._runningRequests.removeByRequest(request)

    def _takeJob(self):
        patchNr = self._queue.pop()
        
        rect = self._imagePatches[0][patchNr].imageRect
        
        for layerNr in range(len(self._stackedIms)):
            layer = self._stackedIms[layerNr]
            imageSource = self._stackedIms._layerToIms[layer]
            if layer.visible:
                request = imageSource.request(rect)
                self._runningRequests.addRequest(patchNr, request)
                request.notify(self._onPatchFinished, request=request, patchNumber=patchNr, patchLayer=layerNr)

    def _runImpl(self):
        self._dataPending.wait()
        while len(self._queue) > 0:
            self._takeJob()
        self._dataPending.clear()
    
    def run(self):
        while not self._stopped:
            self._runImpl()

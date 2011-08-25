from PyQt4.QtCore import QThread, pyqtSignal, Qt, QMutex
from PyQt4.QtGui import QPainter

import threading, copy
from collections import deque

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************

class Requests(object):
    def __init__(self):
        self._mutex = QMutex()
        self._id2r  = dict()
        self._r     = set()

    def addRequest(self, id, request):
        self._mutex.lock()
        
        if not id in self._id2r:
            self._id2r[id] = []
        self._id2r[id].append(request)
        self._r.add(request)
        
        self._mutex.unlock()
        
    def removeById(self, id):
        self._mutex.lock()
        if id in self._id2r:
            for req in self._id2r[id]:
                self._r.remove(req)
                req.cancel()
            del self._id2r[id]
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
            id = (id for id,r in self._id2r.items() if req in r).next()
            self._id2r[id].remove(req)
            self._r.remove(req)
            req.cancel()
        self._mutex.unlock()

class ImageSceneRenderThread(QThread):
    """
    Composites individual tiles. For one tile,
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
    
    def __init__(self, imagePatches, stackedImageSources, parent = None):
        assert hasattr(stackedImageSources, '__iter__')
        QThread.__init__(self, parent)
        self._imagePatches = imagePatches

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
        self._stopped = True
        self._dataPending.set()
        self.wait()

    def cancelAll(self):
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
        
        thisPatch = self._imagePatches[patchNumber][patchLayer]
        
        ### one layer of this patch is done, just assign the newly arrived image
        thisPatch.image = image
        ### ...done
        
        numLayers      = len(self._imagePatches[patchNumber])-1
        compositePatch = self._imagePatches[patchNumber][numLayers]
    
        ### render the composite patch ######             
        compositePatch.mutex.lock()
        compositePatch.dirty = True
        p = QPainter(compositePatch.image)
        r = compositePatch.rect
        p.fillRect(0,0,r.width(), r.height(), Qt.white)

        for layerNr, patch in enumerate(self._imagePatches[patchNumber][:-1]):
            if not self._stackedIms[layerNr].visible:
                continue
            p.setOpacity(self._stackedIms[layerNr].opacity)
            p.drawImage(0,0, patch.image)
        p.end()
        compositePatch.dirty = False
        compositePatch.mutex.unlock()
        ### ...done rendering ################
        
        self.patchAvailable.emit(patchNumber)
        
        request.cancelUnlock()
        
        #Now that the lock has been released, we can remove the (done)
        #request (which will lock the request again)
        self._runningRequests.removeByRequest(request)

    def _takeJob(self):
        patchNr = self._queue.pop()
        
        rect = self._imagePatches[patchNr][0].rect
        
        for layerNr, (opacity, visible, imageSource) in enumerate(self._stackedIms):
            if self._stackedIms[layerNr].visible:
                request = imageSource.request(rect)
                self._runningRequests.addRequest(patchNr, request)
                request.notify(self._onPatchFinished, request = request, patchNumber=patchNr, patchLayer=layerNr)

    def _runImpl(self):
        self._dataPending.wait()
        while len(self._queue) > 0:
            self._takeJob()
        self._dataPending.clear()
    
    def run(self):
        while not self._stopped:
            self._runImpl()

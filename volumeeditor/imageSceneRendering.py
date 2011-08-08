from PyQt4.QtCore import QThread, pyqtSignal, Qt
from PyQt4.QtGui import QPainter

import threading, time
from collections import deque, namedtuple

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************

class ImageSceneRenderThread(QThread):
    """
    Composites individual tiles. For one tile,
    it requests the corresponding region for all the
    visible layers in the layerstack as QImage objects,
    and then users alpha blending to arrive at a final
    output image.
    
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
        self._runningRequests = set()


    def synchronousRequestPatch(self, patchNr):
        numLayers = len(self._imagePatches[patchNr])-1
        temp = []
        rect = self._imagePatches[patchNr][0].rect
        
        for layerNr, (opacity, visible, imageSource) in enumerate(self._stackedIms):
            if self._stackedIms[layerNr].visible:
                request = imageSource.request(rect)
                temp.append((request, layerNr))
        
        compositePatch = self._imagePatches[patchNr][numLayers]
        p = QPainter(compositePatch.image)
        r = compositePatch.rect
        p.fillRect(0,0,r.width(), r.height(), Qt.white)
        
        for req,layerNr in temp:
            img = req.wait()
            p.setOpacity(self._stackedIms[layerNr].opacity)
            p.drawImage(0,0, img)
        p.end()
        
        return compositePatch.image


    def requestPatch(self, patchNr):
        if patchNr not in self._queue:
            self._queue.append(patchNr)
            self._dataPending.set()

    def stop(self):
        self._stopped = True
        self._dataPending.set()
        self.wait()

    def cancelAll(self):
        temp = self._runningRequests
        self._runningRequests = set()
        for r in temp:
            r.cancel()

    def _takeJob(self):
        patchNr = self._queue.pop()
        
        rect = self._imagePatches[patchNr][0].rect
        
        def onPatchFinished(image, request, patchNumber, patchLayer):
            thisPatch = self._imagePatches[patchNumber][patchLayer]
            
            ### one layer of this patch is done, just assign the newly arrived image
            thisPatch.mutex.lock()
            thisPatch.image = image
            thisPatch.mutex.unlock()
            ### ...done
            
            numLayers      = len(self._imagePatches[patchNr])-1
            compositePatch = self._imagePatches[patchNr][numLayers]
        
            ### render the composite patch             
            compositePatch.mutex.lock()
            compositePatch.dirty = True
        
            p = QPainter(compositePatch.image)
            r = compositePatch.rect
            p.fillRect(0,0,r.width(), r.height(), Qt.white)
    
            for layerNr, patch in enumerate(self._imagePatches[patchNr][:-1]):
                if not self._stackedIms[layerNr].visible:
                    continue
                p.setOpacity(self._stackedIms[layerNr].opacity)
                p.drawImage(0,0, patch.image)
            p.end()
            
            compositePatch.dirty = False
            try:
                self._runningRequests.remove(request)
            except:
                pass
            compositePatch.mutex.unlock()
            ### ...done rendering
            
            self.patchAvailable.emit(patchNr)
        
        for layerNr, (opacity, visible, imageSource) in enumerate(self._stackedIms):
            if self._stackedIms[layerNr].visible:
                request = imageSource.request(rect)
                self._runningRequests.add(request)
                request.notify(onPatchFinished, request = request, patchNumber=patchNr, patchLayer=layerNr)

    def _runImpl(self):
        self._dataPending.wait()
        while len(self._queue) > 0:
            self._takeJob()
        self._dataPending.clear()
    
    def run(self):
        while not self._stopped:
            self._runImpl()

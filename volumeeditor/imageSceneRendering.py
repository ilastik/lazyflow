from PyQt4.QtCore import QThread, pyqtSignal, Qt
from PyQt4.QtGui import QPainter

import threading
from collections import deque, namedtuple

class ImageSceneRenderThread(QThread):
    patchAvailable = pyqtSignal(int)
    
    def __init__(self, imagePatches, imageSourceStack, parent = None):
        assert hasattr(imageSourceStack, '__iter__')
        QThread.__init__(self, parent)
        self._imagePatches = imagePatches

        self._queue = deque()
        
        self._dataPending = threading.Event()
        self._dataPending.clear()
        self._stopped = False

        self._imsStack = imageSourceStack

    def requestPatch(self, patchNr):
        if patchNr not in self._queue:
            self._queue.append(patchNr)
            self._dataPending.set()

    def stop(self):
        self._stopped = True
        self._dataPending.set()
        self.wait()

    def _takeJob(self):
        patchNr = self._queue.pop()
        
        patch = self._imagePatches[patchNr]
        patch.rendering = True

        #
        # alpha blending of layers
        #
        # request image for every layer to allow parallel background computations 
        requestStack = [ (entry[0], entry[1].request(patch.rect)) for entry in self._imsStack ]

        # before the first layer is painted, initialize it white to enable sound alpha blending
        p = QPainter(patch.image)
        r = patch.rect
        p.fillRect(0,0,r.width(), r.height(), Qt.white)

        for entry in requestStack:
            p.setOpacity(entry[0])
            img = entry[1].wait()
            p.drawImage(0,0, img)
        p.end()
        
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

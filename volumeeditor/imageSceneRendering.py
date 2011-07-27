from PyQt4.QtCore import QThread, pyqtSignal, QPoint, QSize, Qt
from PyQt4.QtGui import QPainter, QColor, QImage

import numpy, qimage2ndarray
import threading
from collections import deque

class ImageSceneRenderThread(QThread):
    patchAvailable = pyqtSignal(int)
    
    def __init__(self, imagePatches, imageSourcesStack, parent = None):
        assert hasattr(imageSourcesStack, '__iter__')
        QThread.__init__(self, parent)
        self._imagePatches = imagePatches

        self._queue = deque()
        
        self._dataPending = threading.Event()
        self._dataPending.clear()
        self._stopped = False

        self._imsStack = imageSourcesStack

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

        p = QPainter(patch.image)
        r = patch.rect

        for index, opacity_src in enumerate(self._imsStack):
            # before the first layer is painted, initialize it white to enable sound alpha blending
            if index == 0:
                p.fillRect(0,0,r.width(), r.height(), Qt.white)

            p.setOpacity(opacity_src[0])
            img = opacity_src[1].request(patch.rect).wait()
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

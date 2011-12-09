"""High-level API.

"""
from volumina.pixelpipeline.datasources import *
from volumina.layer import *
from volumina.layerstack import LayerStackModel
from volumina.volumeEditor import VolumeEditor

from PyQt4.QtCore import QRectF
from PyQt4.QtGui import QMainWindow, QApplication, QIcon, QAction, qApp, \
    QImage, QPainter
from PyQt4.uic import loadUi
import volumina.icons_rc

import os
import sys
import numpy
import colorsys
import random
import vigra

haveLazyflow = True
try:
    from volumina.lazyflowBridge import Op5ifyer
except ImportError:
    haveLazyflow = False

#******************************************************************************
# V i e w e r                                                                 *
#******************************************************************************

class Viewer(QMainWindow):
    """High-level API to view multi-dimensional arrays.

    Properties:
        title -- window title
    """

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        uiDirectory = os.path.split(volumina.__file__)[0]
        if uiDirectory == '':
            uiDirectory = '.'
        loadUi(uiDirectory + '/viewer.ui', self)

        self._dataShape = None

        self.layerstack = LayerStackModel()
        self.layerWidget.init(self.layerstack)
        self.editor = VolumeEditor(self.layerstack, labelsink=None)
        self.volumeEditorWidget.init(self.editor)
        self.layerstack = self.editor.layerStack

        self.layerWidget.setModel(self.layerstack)
        model = self.layerstack
        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)

        self.actionQuit.triggered.connect(qApp.quit)

        w = self.volumeEditorWidget
        self.menuView.addAction(w.allZoomToFit)
        self.menuView.addAction(w.allToggleHUD)
        self.menuView.addAction(w.allCenter)
        self.menuView.addSeparator()
        self.actionOnly_for_current_view = QAction(QIcon(), \
            "Only for selected view", self.menuView)
        f = self.actionOnly_for_current_view.font()
        f.setBold(True)
        self.actionOnly_for_current_view.setFont(f)
        self.menuView.addAction(self.actionOnly_for_current_view)
        self.menuView.addAction(w.selectedZoomToFit)
        self.menuView.addAction(w.toggleSelectedHUD)
        self.menuView.addAction(w.selectedCenter)
        self.menuView.addAction(w.selectedZoomToOriginal)
        self.menuView.addAction(w.rubberBandZoom)

        self.editor.newImageView2DFocus.connect(self._setIconToViewMenu)

        self._renderScreenshotDisconnect = None

    def _setIconToViewMenu(self):
        focused = self.editor.imageViews[self.editor._lastImageViewFocus]
        self.actionOnly_for_current_view.setIcon(\
            QIcon(focused._hud.axisLabel.pixmap()))

    def randomColors(self, M=256):
        colors = []
        for i in range(M):
            if i == 0:
                colors.append(QColor(0, 0, 0, 0).rgba())
            else:
                h, s, v = random.random(), random.random(), 1.0
                color = numpy.asarray(colorsys.hsv_to_rgb(h, s, v)) * 255
                qColor = QColor(*color)
                colors.append(qColor.rgba())
        return colors

    def renderScreenshot(self, axis, blowup=1, filename="/tmp/volumina_screenshot.png"):
        """Save the complete slice as shown by the slice view 'axis'
        in the GUI as an image
        
        axis -- 0, 1, 2 (x, y, or z slice view)
        blowup -- enlarge written image by this factor
        filename -- output file
        """

        print "Rendering screenshot for axis=%d to '%s'" % (axis, filename)
        s = self.editor.imageScenes[axis]
        self.editor.navCtrl.enableNavigation = False
        func = partial(self._renderScreenshot, s, blowup, filename)
        self._renderScreenshotDisconnect = func
        s._renderThread.patchAvailable.connect(func)
        nRequested = 0
        for patchNumber in range(len(s._tiling)):
            p = s.tileProgress(patchNumber)
            if p < 1.0:
                s.requestPatch(patchNumber)
                nRequested += 1
        print "  need to compute %d of %d patches" % (nRequested, len(s._tiling))
        if nRequested == 0:
            #If no tile needed to be requested, the 'patchAvailable' signal
            #of the render thread will never come.
            #In this case, we need to call the implementation ourselves:
            self._renderScreenshot(s, blowup, filename, patchNumber=0)

    def _renderScreenshot(self, s, blowup, filename, patchNumber):
        progress = 0
        for patchNumber in range(len(s._tiling)):
            p = s.tileProgress(patchNumber) 
            progress += p
        progress = progress/float(len(s._tiling))
        if progress == 1.0:
            s._renderThread.patchAvailable.disconnect(self._renderScreenshotDisconnect)
            
            img = QImage(int(round((blowup*s.sceneRect().size().width()))),
                         int(round((blowup*s.sceneRect().size().height()))),
                         QImage.Format_ARGB32)
            screenshotPainter = QPainter(img)
            screenshotPainter.setRenderHint(QPainter.Antialiasing, True)
            s.render(screenshotPainter, QRectF(0, 0, img.width()-1, img.height()-1), s.sceneRect())
            print "  saving to '%s'" % filename
            img.save(filename)
            del screenshotPainter
            self.editor.navCtrl.enableNavigation = True

    def addLayer(self, a, display='grayscale', opacity=1.0, \
                 name='Unnamed Layer', visible=True):
        Source = ArraySource
        if hasattr(a, '_metaParent'):
            #this is a lazyflow OutputSlot object
            Source = LazyflowSource
            if len(a.shape) == 3:
                print "lazyflow input has shape %r" % (a.shape,)
                o = Op5ifyer(a.operator.graph)
                o.inputs['Input'].connect(a)
                a = o.outputs['Output']
                print "  -> new shape: %r" % (a.shape,)
        elif hasattr(a, 'axistags'):
            #vigra array with axistags
            a = a.withAxes('t', 'x', 'y', 'z', 'c')
        elif a.ndim != 5:
            #numpy array; no axistags available
            if a.ndim != 3:
                raise RuntimeError("Cannot convert to 5D array: shape=%r" \
                                   % a.shape)
            a = a[numpy.newaxis, ..., numpy.newaxis]

        if self.editor.dataShape != a.shape or len(self.layerstack) == 0:
            self.layerstack.clear()
            self.editor.dataShape = a.shape

        if display == 'grayscale':
            source = Source(a)
            layer = GrayscaleLayer(source)
        elif display == 'randomcolors':
            if a.dtype != numpy.uint8:
                print "layer '%s': implicit conversion from %s to uint8" \
                      % (name, a.dtype)
                if a.dtype == numpy.uint32:
                    a = a.astype(numpy.uint8)
                else:
                    raise RuntimeError("unhandled dtype=%r" % a.dtype)
            source = Source(a)
            layer = ColortableLayer(source, self.randomColors())
        else:
            raise RuntimeError("unhandled type of overlay")
        layer.name = name
        layer.opacity = opacity
        layer.visible = visible
        self.layerstack.append(layer)

    @property
    def title(self):
        return self.windowTitle()

    @title.setter
    def title(self, t):
        self.setWindowTitle(t)

#******************************************************************************
#* if __name__ == '__main__':                                                 *
#******************************************************************************

if __name__ == '__main__':

    if haveLazyflow:
        from lazyflow.graph import Operator, OutputSlot, InputSlot

        class OpOnDemand(Operator):
            name = "OpOnDemand"
            category = "Debug"

            inputSlots = [InputSlot('shape')]
            outputSlots = [OutputSlot("output")]

            def notifyConnectAll(self):
                print "notifyConnectAll"
                oslot = self.outputs['output']
                oslot._shape = self.inputs['shape'].value
                oslot._dtype = numpy.uint8
                oslot._axistags = vigra.defaultAxistags(len(oslot._shape))

            def getOutSlot(self, slot, key, result):
                result[:] = numpy.random.randint(0, 255)

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    v = Viewer()
    v.show()

    d = (numpy.random.random((1000, 800, 50)) * 255).astype(numpy.uint8)
    assert d.ndim == 3

    #FIXME: this does not work
    #d = d.view(vigra.VigraArray)

    v.addLayer(d, display='randomcolors', name="numpy 3D", visible=True)
    v.addLayer(d[numpy.newaxis, ..., numpy.newaxis], display='randomcolors', \
               name="numpy 5D", visible=False)

    v.title = 'My Data Example'
    if haveLazyflow:
        g = Graph()
        op = OpOnDemand(g)
        op.inputs['shape'].setValue(d.shape)
        v.addLayer(op.outputs['output'], name='lazyflow 3D', visible=False)
        op2 = OpOnDemand(g)
        op2.inputs['shape'].setValue((1,) + d.shape + (1,))
        v.addLayer(op2.outputs['output'], name='lazyflow 5D', visible=False)

    app.exec_()

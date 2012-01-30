from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon

import numpy

from lazyflow.graph import Graph
from volumina.volumeEditor import VolumeEditor
from volumina.volumeEditorWidget import VolumeEditorWidget
from volumina.pixelpipeline.datasources import ArraySource
from volumina.layerstack import LayerStackModel
from volumina.layer import GrayscaleLayer

class PyVolumeEditorWidgetPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        a = (numpy.random.random((1,100,200,300,1))*255).astype(numpy.uint8)
        source = ArraySource(a)
        layerstack = LayerStackModel()
        layerstack.append( GrayscaleLayer( source ) )

        editor = VolumeEditor(layerstack, labelsink=None)  
        widget = VolumeEditorWidget(parent=parent)
        widget.init(editor)
        editor.dataShape = a.shape
        return widget
    
    def name(self):
        return "VolumeEditorWidget"

    def group(self):
        return "ilastik widgets"
    
    def icon(self):
        return QIcon(QPixmap(16,16))
                           
    def toolTip(self):
        return ""
    
    def whatsThis(self):
        return ""
    
    def isContainer(self):
        return False
    
    def domXml(self):
        return (
               '<widget class="VolumeEditorWidget" name=\"volumeEditorWidget\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "volumina.volumeEditorWidget"

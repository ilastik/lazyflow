from PyQt4 import QtGui, QtDesigner
from volumeeditor.volumeEditorWidget import *
from volumeeditor.layerstack import LayerStackModel


from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from volumeeditor.pixelpipeline.datasources import LazyflowSource, ConstantSource
from volumeeditor.pixelpipeline._testing import OpDataProvider
from volumeeditor._testing.from_lazyflow import OpDataProvider5D, OpDelay
from volumeeditor.layer import GrayscaleLayer, RGBALayer, ColortableLayer
from volumeeditor.layerwidget.layerwidget import LayerWidget
from volumeeditor.layerstack import LayerStackModel


class PyVolumeEditorWidgetPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):
    
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)

        self.initialized = False
        
    def initialize(self, core):

        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):

        return self.initialized
    
    def createWidget(self, parent):
        print "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDAAAAAA"
        g = Graph()
        layerstack = LayerStackModel()
        N=100
        hugeslab = (numpy.random.rand(1,N,2*N, 10,1)*255).astype(numpy.uint8)
        shape = hugeslab.shape
                
        op1 = OpDataProvider(g, hugeslab)
        op2 = OpDelay(g, 0.000003)
        op2.inputs["Input"].connect(op1.outputs["Data"])
        source = LazyflowSource(op2.outputs["Output"])
        layers = [GrayscaleLayer( source )]
        
        layerstack.append( GrayscaleLayer( source ) )

        editor = VolumeEditor(shape, layerstack, labelsink=None, useGL=False)  
        widget = VolumeEditorWidget(parent=parent)
        widget.init(editor)
        print "RETURNING ", widget
        return widget
    
    def name(self):
        return "VolumeEditorWidget"

    def group(self):
        return "ilastik widgets"
    
    def isContainer(self):
        return False
    
    def domXml(self):
        return (
               '<widget class="VolumeEditorWidget" name=\"volumeEditorWidget\">\n'
               " <property name=\"toolTip\" >\n"
               "  <string>The current time</string>\n"
               " </property>\n"
               " <property name=\"whatsThis\" >\n"
               "  <string>The analog clock widget displays "
               "the current time.</string>\n"
               " </property>\n"
               "</widget>\n"
               )
    
    def includeFile(self):
        return "volumeeditor.volumeEditorWidget"
    
    
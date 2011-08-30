from PyQt4.QtGui import QStyledItemDelegate, QWidget, QListView, QStyle, \
                        QAbstractItemView, QPainter, QItemSelectionModel, \
                        QColor, QMenu, QAction, QFontMetrics, QFont, QImage, \
                        QBrush, QPalette
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, QRect, QSize, QTimer, \
                         QPoint 
                         
from volumeeditor.layer import Layer

from os import path
import volumeeditor.resources.icons
from volumeeditor.layerstack import LayerStackModel
_icondir = path.dirname(volumeeditor.resources.icons.__file__)

#*******************************************************************************
# L a y e r P a i n t e r                                                      *
#*******************************************************************************

class LayerPainter( object ):
    def __init__(self ):
        self.layer = None
        
        self.rect = QRect()
        
        self.fm = QFontMetrics(QFont())
        
        self.iconSize = 20
        self.iconXOffset = 5
        self.textXOffset = 5
        self.progressXOffset = self.iconXOffset+self.iconSize+self.textXOffset
        self.progressYOffset = self.iconSize+5
        self.progressHeight = 10
        
        self.alphaTextWidth = self.fm.boundingRect(u"\u03B1=100.0%").width()
        

    def sizeHint(self):
        if self.layer.mode == 'ReadOnly':
            return QSize(1,self.fm.height()+5)
        elif self.layer.mode == 'Expanded' or self.layer.mode == 'Editable':
            return QSize(1,self.progressYOffset+self.progressHeight+5)
        else:
            raise RuntimeError("Unknown mode")   

    def overEyeIcon(self, x, y):
        return QPoint(x,y) in QRect(self.iconXOffset,0,self.iconSize,self.iconSize)

    def percentForPosition(self, x, y, checkBoundaries=True):
        if checkBoundaries and (y < self.progressYOffset or y > self.progressYOffset + self.progressHeight) \
                           or  (x < self.progressXOffset):
            return -1
        
        percent = (x-self.progressXOffset)/float(self._progressWidth)
        if percent < 0:
            return 0.0
        if percent > 1:
            return 1.0
        return percent

    @property
    def _progressWidth(self):
        return self.rect.width()-self.progressXOffset-10

    def paint(self, painter, rect, palette, mode):
        if not self.layer.visible:
            palette.setCurrentColorGroup(QPalette.Disabled)
        
        self.rect = rect
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(rect.x(), rect.y())
        painter.setFont(QFont())
        
        painter.setBrush(palette.text())
        
        if mode != 'ReadOnly':
            painter.save()
            painter.setBrush(palette.highlight())
            painter.drawRect(rect)
            painter.restore()
        
        textOffsetX = self.progressXOffset
        textOffsetY = max(self.fm.height()-self.iconSize,0)/2.0+self.fm.height()
        
        if self.layer.visible:
            painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), \
                              QImage(path.join(_icondir, "stock-eye-20.png")))
        else:
            painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), \
                              QImage(path.join(_icondir, "stock-eye-20-gray.png")))

        #layer name text
        if mode != 'ReadOnly':
            painter.setBrush(palette.highlightedText())
        else:
            painter.setBrush(palette.text())
        
        #layer name
        painter.drawText(QPoint(textOffsetX, textOffsetY), "%s" % self.layer.name)
        #opacity
        text = u"\u03B1=%0.1f%%" % (100.0*(self.layer.opacity))
        painter.drawText(QPoint(textOffsetX+self._progressWidth-self.alphaTextWidth, textOffsetY), text)
        
        if mode != 'ReadOnly':  
            #frame around percentage indicator
            painter.setBrush(palette.dark())
            painter.save()
            #no fill color
            b = painter.brush(); b.setStyle(Qt.NoBrush); painter.setBrush(b)
            painter.drawRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(self._progressWidth, self.progressHeight)))
            painter.restore()
        
            #percentage indicator
            painter.drawRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(self._progressWidth*self.layer.opacity, self.progressHeight)))
            
        painter.restore()

#*******************************************************************************
# L a y e r D e l e g a t e                                                    *
#*******************************************************************************

class LayerDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)
        self.currentIndex = -1
        self._layerPainter = LayerPainter()
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
    
    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            modelIndex = index.row()
            if modelIndex != self.currentIndex:
                model = index.model()
                self.currentIndex = modelIndex
                model.wantsUpdate()
        
        layer = index.data().toPyObject()
        if isinstance(layer, Layer):
            self._layerPainter.layer = layer
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, QColor(0,255,0,10))
                self._layerPainter.paint(painter, option.rect, option.palette, 'Expanded')
            else:
                self._layerPainter.paint(painter, option.rect, option.palette, 'ReadOnly')
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        layer = index.data().toPyObject()
        if isinstance(layer, Layer):
            self._layerPainter.layer = layer
            return self._layerPainter.sizeHint()
        else:
            return QStyledItemDelegate.sizeHint(self, option, index)
    
    def createEditor(self, parent, option, index):
        layer = index.data().toPyObject()
        if isinstance(layer, Layer):
            return LayerEditor(parent)
        else:
            QStyledItemDelegate.createEditor(self, parent, option, index)
        
    def setEditorData(self, editor, index):
        layer = index.data().toPyObject()
        if isinstance(layer, Layer):
            editor.layer = layer
        else:
            QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        layer = index.data().toPyObject()
        if isinstance(layer, Layer):
            model.setData(index, editor.layer)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, index)

    def commitAndCloseEditor(self):
        editor = sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

#*******************************************************************************
# L a y e r E d i t o r                                                        *
#*******************************************************************************

class LayerEditor(QWidget):
    editingFinished = pyqtSignal()
    
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.lmbDown = False
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        self._layerPainter = LayerPainter()
        self._layer = None
        
    @property
    def layer(self):
        return self._layer
    @layer.setter
    def layer(self, layer):
        if self._layer:
            self._layer.changed.disconnect()
        self._layer = layer
        self._layer.changed.connect(self.repaint)
        self._layerPainter.layer = layer
    
    def minimumSize(self):
        return self.sizeHint()
    
    def maximumSize(self):
        return self.sizeHint()
        
    def paintEvent(self, e):
        painter = QPainter(self)
        self._layerPainter.paint(painter, self.rect(), self.palette(), 'Editable')
        
    def mouseMoveEvent(self, event):
        if self.lmbDown:
            opacity = self._layerPainter.percentForPosition(event.x(), event.y(), checkBoundaries=False)
            if opacity >= 0:
                self.layer.opacity = opacity
                self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return
        
        self.lmbDown = True
        
        if self._layerPainter.overEyeIcon(event.x(), event.y()):
            self._layer.visible = not self._layer.visible
            self.update()
        
        opacity = self._layerPainter.percentForPosition(event.x(), event.y())
        if opacity >= 0:
            self._layer.opacity = opacity
            self.update()

    def mouseReleaseEvent(self, event):
        self.lmbDown = False

#*******************************************************************************
# L a y e r W i d g e t                                                        *
#*******************************************************************************

class LayerWidget(QListView):
    def __init__(self, parent = None, model=None):
        
        QListView.__init__(self, parent)

        if model is None:
            model = LayerStackModel()
        self.init(model)

    def init(self, listModel):
        self.setModel(listModel)
        self.setItemDelegate(LayerDelegate())
        self.setSelectionModel(listModel.selectionModel)
        #self.setDragDropMode(self.InternalMove)
        self.installEventFilter(self)
        #self.setDragDropOverwriteMode(False)
        self.model().selectionModel.selectionChanged.connect(self.onSelectionChanged)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContext)
        QTimer.singleShot(0, self.selectFirstEntry)
    
    def resizeEvent(self, e):
        self.updateGUI()
        QListView.resizeEvent(self, e)
    
    def onContext(self, pos):        
        idx = self.indexAt(pos)
        layer = self.model()[idx.row()]
        print "Context menu for layer '%s'" % layer.name
        
        layer.contextMenu(self, self.mapToGlobal(pos))
            
    def selectFirstEntry(self):
        #self.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.model().selectionModel.setCurrentIndex(self.model().index(0), QItemSelectionModel.SelectCurrent)
        self.updateGUI()
    
    def updateGUI(self):
        self.openPersistentEditor(self.model().selectedIndex())
    
    def eventFilter(self, sender, event):
        #http://stackoverflow.com/questions/1224432/
        #how-do-i-respond-to-an-internal-drag-and-drop-operation-using-a-qlistwidget
        if (event.type() == QEvent.ChildRemoved):
            self.onOrderChanged()
        return False
    
    def onSelectionChanged(self, selected, deselected):
        if len(deselected) > 0:
            self.closePersistentEditor(deselected[0].indexes()[0])
        self.updateGUI()
    
    def onOrderChanged(self):
        self.updateGUI()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys, numpy

    from PyQt4.QtGui import QApplication, QPushButton, QHBoxLayout, QVBoxLayout

    app = QApplication(sys.argv)
            
    model = LayerStackModel()
    
    o1 = Layer()
    o1.name = "Fancy Layer"
    o1.opacity = 0.5
    model.append(o1)
    
    o2 = Layer()
    o2.name = "Some other Layer"
    o2.opacity = 0.25
    model.append(o2)
    
    o3 = Layer()
    o3.name = "Invisible Layer"
    o3.opacity = 0.15
    o3.visible = False
    model.append(o3)
    
    o4 = Layer()
    o4.name = "Fancy Layer II"
    o4.opacity = 0.95
    model.append(o4)
    
    o5 = Layer()
    o5.name = "Fancy Layer III"
    o5.opacity = 0.65
    model.append(o5)

    view = LayerWidget(None, model)
    view.show()
    view.updateGeometry()

    w = QWidget()
    lh = QHBoxLayout(w)
    lh.addWidget(view)
    
    up   = QPushButton('Up')
    down = QPushButton('Down')
    delete = QPushButton('Delete')
    add = QPushButton('Add')
    lv  = QVBoxLayout()
    lh.addLayout(lv)
    
    lv.addWidget(up)
    lv.addWidget(down)
    lv.addWidget(delete)
    lv.addWidget(add)
    
    w.setGeometry(100, 100, 800,600)
    w.show()
    
    up.clicked.connect(model.moveSelectedUp)
    model.canMoveSelectedUp.connect(up.setEnabled)
    down.clicked.connect(model.moveSelectedDown)
    model.canMoveSelectedDown.connect(down.setEnabled)
    delete.clicked.connect(model.deleteSelected)
    model.canDeleteSelected.connect(delete.setEnabled)
    def addRandomLayer():
        o = Layer()
        o.name = "Layer %d" % (model.rowCount()+1)
        o.opacity = numpy.random.rand()
        o.visible = bool(numpy.random.randint(0,2))
        model.append(o)
    add.clicked.connect(addRandomLayer)

    app.exec_()

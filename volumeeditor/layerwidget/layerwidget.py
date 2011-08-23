from PyQt4.QtGui import QStyledItemDelegate, QWidget, QListView, QStyle, \
                        QAbstractItemView, QPainter, QItemSelectionModel, \
                        QColor, QMenu, QAction, QFontMetrics, QFont, QImage, \
                        QBrush
from PyQt4.QtCore import pyqtSignal, Qt, QEvent, QRect, QSize, QTimer, \
                         QPoint 
                         
from volumeeditor.layer import Layer

from os import path
import volumeeditor.resources.icons
_icondir = path.dirname(volumeeditor.resources.icons.__file__)

#*******************************************************************************
# L a y e r P a i n t e r                                                      *
#*******************************************************************************

class LayerPainter( object ):
    def __init__(self ):
        self.layer = None
        
        self.rect = QRect()
        
        self.fm = QFontMetrics(QFont())
        
        self.iconSize = 22
        self.iconXOffset = 5
        self.textXOffset = 5
        self.progressXOffset = 15
        self.progressYOffset = self.iconSize+5
        self.progressHeight = 10

    def sizeHint(self):
        if self.layer.mode == 'ReadOnly':
            return QSize(1,self.fm.height()+5)
        elif self.layer.mode == 'Expanded' or self.layer.mode == 'Editable':
            return QSize(1,self.progressYOffset+self.progressHeight+5)
        else:
            raise RuntimeError("Unknown mode")   

    def overEyeIcon(self, x, y):
        return QPoint(x,y) in QRect(self.iconXOffset,0,self.iconSize,self.iconSize)

    def percentForPosition(self, x, y):
        if y < self.progressYOffset or y > self.progressYOffset + self.progressHeight:
            return -1
        
        percent = (x-self.progressXOffset)/float(self.rect.width()-2*self.progressXOffset)
        if percent < 0:
            return 0.0
        if percent > 1:
            return 1.0
        return percent

    def paint(self, painter, rect, palette, mode):
        self.rect = rect
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(rect.x(), rect.y())
        painter.setFont(QFont())
        
        if self.layer.visible:
            painter.setPen(QColor(0,0,0))
        else:
            painter.setPen(QColor(0,0,0,90))
        
        if mode == 'ReadOnly':
            text = "[%3d%%] %s" % (int(100.0 * self.layer.opacity), self.layer.name)
            painter.drawText(QPoint(5, self.fm.height()), text)
        else:
            if self.layer.visible:
                painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), \
                                  QImage(path.join(_icondir, "layer-visible-on.png")))
            else:
                painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), \
                                  QImage(path.join(_icondir, "layer-visible-off.png")))
            text = "%s" % self.layer.name
            painter.drawText(QPoint(self.iconXOffset+self.iconSize+self.textXOffset,\
                                    max(self.fm.height()-self.iconSize,0)/2.0+self.fm.height()),\
                             text)
            
            w = rect.width()-2*self.progressXOffset
            
            painter.drawRoundedRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(w, self.progressHeight)), self.progressHeight/2, self.progressHeight/2)
            painter.setBrush(QBrush(QColor(0,0,0)))
            
            if not self.layer.visible: painter.setBrush(QBrush(QColor(0,0,0,80)))
            painter.drawEllipse(QRect(self.progressXOffset+(w-self.progressHeight)*self.layer.opacity, \
                                      self.progressYOffset, self.progressHeight, self.progressHeight))
            
            painter.setPen(Qt.NoPen)
            if self.layer.visible: painter.setBrush(QBrush(QColor(0,0,255,50))) 
            else: painter.setBrush(QBrush(QColor(0,0,0,20)))
            painter.drawRoundedRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(w*self.layer.opacity, self.progressHeight)), \
                                                self.progressHeight/2, self.progressHeight/2)
            
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
        self._layer = layer
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
            opacity = self._layerPainter.percentForPosition(event.x(), event.y())
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
    def __init__(self, parent = None, listModel=None):
        
        QListView.__init__(self, parent)
        if listModel:
          self.init(listModel)
        
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
    
    def onContext(self, point):
        menu = QMenu("Menu", self)
        a = QAction("aaa", menu)
        b = QAction("bbb", menu)
        menu.addAction(a)
        menu.addAction(b)
        menu.exec_(self.mapToGlobal(point))
    
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

    import sys
    from volumeeditor.layerstack import LayerStackModel, Layer

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

    view = LayerWidget(model)
    view.show()
    view.updateGeometry()

    w = QWidget()
    lh = QHBoxLayout(w)
    lh.addWidget(view)
    
    up   = QPushButton('Up')
    down = QPushButton('Down')
    delete = QPushButton('Delete')
    lv  = QVBoxLayout()
    lh.addLayout(lv)
    
    lv.addWidget(up)
    lv.addWidget(down)
    lv.addWidget(delete)
    
    w.setGeometry(100, 100, 800,600)
    w.show()
    
    up.clicked.connect(model.moveSelectedUp)
    model.canMoveSelectedUp.connect(up.setEnabled)
    down.clicked.connect(model.moveSelectedDown)
    model.canMoveSelectedDown.connect(down.setEnabled)
    delete.clicked.connect(model.deleteSelected)
    model.canDeleteSelected.connect(delete.setEnabled)

    app.exec_()

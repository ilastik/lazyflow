from PyQt4.QtGui import QStyledItemDelegate, QWidget, QListView, QStyle, \
                        QAbstractItemView, QPainter, QItemSelectionModel, \
                        QColor, QMenu, QAction
from PyQt4.QtCore import pyqtSignal, Qt, QTimer, QEvent

from volumeeditor.layerstack import LayerParameters

class LayerParametersDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)
        self.currentIndex = -1
    
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
    
    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            modelIndex = index.row()
            if modelIndex != self.currentIndex:
                model = index.model()
                self.currentIndex = modelIndex
                model.wantsUpdate()
        
        layerParameters = index.data().toPyObject()
        if isinstance(layerParameters, LayerParameters):
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, QColor(0,255,0,10))
                layerParameters.paint(painter, option.rect, option.palette, 'Expanded')
            else:
                layerParameters.paint(painter, option.rect, option.palette, 'ReadOnly')
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        layerParameters = index.data().toPyObject()
        if isinstance(layerParameters, LayerParameters):
            return layerParameters.sizeHint()
        else:
            return QStyledItemDelegate.sizeHint(self, option, index)
    
    def createEditor(self, parent, option, index):
        layerParameters = index.data().toPyObject()
        if isinstance(layerParameters, LayerParameters):
            return LayerParametersEditor(parent)
        else:
            QStyledItemDelegate.createEditor(self, parent, option, index)
        
    def setEditorData(self, editor, index):
        layerParameters = index.data().toPyObject()
        if isinstance(layerParameters, LayerParameters):
            editor.layerParameters = layerParameters
        else:
            QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        layerParameters = index.data().toPyObject()
        if isinstance(layerParameters, LayerParameters):
            model.setData(index, editor.layerParameters)
        else:
            QStyledItemDelegate.setModelData(self, editor, model, index)

    def commitAndCloseEditor(self):
        editor = sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)



class LayerParametersEditor(QWidget):
    editingFinished = pyqtSignal()
    
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.lmbDown = False
        self.setMouseTracking(True);
        self.setAutoFillBackground(True);
    
    def minimumSize(self):
        return self.sizeHint()
    
    def maximumSize(self):
        return self.sizeHint()
        
    def paintEvent(self, e):
        painter = QPainter(self)
        self.layerParameters.paint(painter, self.rect(), self.palette(), 'Editable')
        
    def mouseMoveEvent(self, event):
        if self.lmbDown:
            opacity = self.layerParameters.percentForPosition(event.x(), event.y())
            if opacity >= 0:
                self.layerParameters.opacity = opacity
                self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return
        
        self.lmbDown = True
        
        if self.layerParameters.overEyeIcon(event.x(), event.y()):
            self.layerParameters.visible = not self.layerParameters.visible
            self.update()
        
        opacity = self.layerParameters.percentForPosition(event.x(), event.y())
        if opacity >= 0:
            self.layerParameters.opacity = opacity
            self.update()

    def mouseReleaseEvent(self, event):
        self.lmbDown = False



class LayerWidget(QListView):
    def __init__(self, listModel, parent = None):
        QListView.__init__(self, parent)
        self.setModel(listModel)
        self.setItemDelegate(LayerParametersDelegate())
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

#------------------------------------------------------------------------------

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    import sys
    from volumeeditor.layerstack import LayerStackModel, LayerParameters

    from PyQt4.QtGui import QApplication, QPushButton, QHBoxLayout, QVBoxLayout

    app = QApplication(sys.argv)
            
    model = LayerStackModel()
    
    o1 = LayerParameters()
    o1.name = "Fancy Layer"
    o1.opacity = 0.5
    model.append(o1)
    
    o2 = LayerParameters()
    o2.name = "Some other Layer"
    o2.opacity = 0.25
    model.append(o2)
    
    o3 = LayerParameters()
    o3.name = "Invisible Layer"
    o3.opacity = 0.15
    o3.visible = False
    model.append(o3)
    
    o4 = LayerParameters()
    o4.name = "Fancy Layer II"
    o4.opacity = 0.95
    model.append(o4)
    
    o5 = LayerParameters()
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

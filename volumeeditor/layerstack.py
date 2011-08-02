from PyQt4.QtCore import *
from PyQt4.QtGui import *
from layer import Layer

from os import path
import resources.icons
_icondir = path.dirname(resources.icons.__file__)

class LayerParameters( object ):
    @property
    def opacity( self ):
        return self.layer.opacity
    @opacity.setter
    def opacity( self, value ):
        self.layer.opacity = value

    @property
    def visible( self ):
        return self.layer.visible
    @visible.setter
    def visible( self, value ):
        self.layer.visible = value

    def __init__(self, layer = Layer()):
        self.mode = 'ReadOnly'
        self.rect = QRect()

        self.layer = layer        
        self.name    = "Unnamed Layer"

        self.fm = QFontMetrics(QFont())
        
        self.iconSize = 22
        self.iconXOffset = 5
        self.textXOffset = 5
        self.progressXOffset = 15
        self.progressYOffset = self.iconSize+5
        self.progressHeight = 10

    def sizeHint(self):
        if self.mode == 'ReadOnly':
            return QSize(1,self.fm.height()+5)
        elif self.mode == 'Expanded' or self.mode == 'Editable':
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
        
        if self.visible:
            painter.setPen(QColor(0,0,0))
        else:
            painter.setPen(QColor(0,0,0,90))
        
        if mode == 'ReadOnly':
            text = "[%3d%%] %s" % (int(100.0 * self.opacity), self.name)
            painter.drawText(QPoint(5, self.fm.height()), text)
        else:
            if self.visible:
                painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), QImage(path.join(_icondir, "layer-visible-on.png")))
            else:
                painter.drawImage(QRect(self.iconXOffset,0,self.iconSize,self.iconSize), QImage(path.join(_icondir, "layer-visible-off.png")))
            text = "%s" % self.name
            painter.drawText(QPoint(self.iconXOffset+self.iconSize+self.textXOffset,max(self.fm.height()-self.iconSize,0)/2.0+self.fm.height()), text)
            
            
            w = rect.width()-2*self.progressXOffset
            
            painter.drawRoundedRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(w, self.progressHeight)), self.progressHeight/2, self.progressHeight/2)
            painter.setBrush(QBrush(QColor(0,0,0)))
            
            if not self.visible: painter.setBrush(QBrush(QColor(0,0,0,80)))
            painter.drawEllipse(QRect(self.progressXOffset+(w-self.progressHeight)*self.opacity, self.progressYOffset, self.progressHeight, self.progressHeight))
            
            painter.setPen(Qt.NoPen)
            if self.visible: painter.setBrush(QBrush(QColor(0,0,255,50)))
            else: painter.setBrush(QBrush(QColor(0,0,0,20)))
            painter.drawRoundedRect(QRect(QPoint(self.progressXOffset, self.progressYOffset), \
                                          QSize(w*self.opacity, self.progressHeight)), self.progressHeight/2, self.progressHeight/2)
            
        painter.restore()

class LayerStackModel(QAbstractListModel):
    canMoveSelectedUp = pyqtSignal("bool")
    canMoveSelectedDown = pyqtSignal("bool")
    canDeleteSelected = pyqtSignal("bool")
    
    orderChanged = pyqtSignal()
    
    def __init__(self, parent = None):
        QAbstractListModel.__init__(self, parent)
        self.layerStack = []
        self.selectionModel = QItemSelectionModel(self)
        self.selectionModel.selectionChanged.connect(self.onSelectionChanged)
        QTimer.singleShot(0, self.updateGUI)
        
    def __repr__(self):
        return "<LayerStackModel: layerStack='%r'>" % (self.layerStack,)
        
    def updateGUI(self):
        self.canMoveSelectedUp.emit(self.selectedRow()>0)
        self.canMoveSelectedDown.emit(self.selectedRow()<self.rowCount()-1)
        self.canDeleteSelected.emit(self.rowCount() > 0)
        self.wantsUpdate()
    
    def append(self, data):
        self.insertRow(self.rowCount())
        self.setData(self.index(self.rowCount()-1), data)
    
    def selectedRow(self):
        selected = self.selectionModel.selectedRows()
        if len(selected) == 1:
            return selected[0].row()
        return -1
    
    def selectedIndex(self):
        row = self.selectedRow()
        if row >= 0:
            return self.index(self.selectedRow())
        else:
            return QModelIndex()
    
    def onSelectionChanged(self, selected, deselected):
        if len(deselected) > 0:
            self.layerStack[deselected[0].indexes()[0].row()].mode = 'ReadOnly'
        if len(selected) > 0:
            self.layerStack[selected[0].indexes()[0].row()].mode = 'Expanded'
        self.updateGUI()
    
    def rowCount(self, parent = QModelIndex()):
        if not parent.isValid():
            return len(self.layerStack)
        return 0
    
    def insertRows(self, row, count, parent = QModelIndex()):
        if parent.isValid():
            return False
        oldRowCount = self.rowCount()
        beginRow = max(0,row)
        endRow   = min(row+count-1, len(self.layerStack))
        self.beginInsertRows(parent, beginRow, endRow) 
        while(beginRow <= endRow):
            self.layerStack.insert(row, LayerParameters())
            beginRow += 1
        self.endInsertRows()
        assert self.rowCount() == oldRowCount+1
        return True
            
    def removeRows(self, row, count, parent = QModelIndex()):
        if parent.isValid():
            return False
        if row+count <= 0 or row >= len(self.layerStack):
            return False
        oldRowCount = self.rowCount()
        beginRow = max(0,row)
        endRow   = min(row+count-1, len(self.layerStack)-1)
        self.beginRemoveRows(parent, beginRow, endRow)
        while(beginRow <= endRow):
            del self.layerStack[row]
            beginRow += 1
        
        self.endRemoveRows()
        assert self.rowCount() == oldRowCount-1
        return True
    
    def flags(self, index):
        defaultFlags = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags
    
    def supportedDropActions(self):
        return Qt.MoveAction
    
    def data(self, index, role):
        if not index.isValid():
            return None
        if index.row() > len(self.layerStack):
            return None
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.layerStack[index.row()]
        
        return None
    
    def setData(self, index, value, role = Qt.EditRole):
        overlayParameters = value
        if not isinstance(value, LayerParameters):
            overlayParameters = value.toPyObject()
        
        self.layerStack[index.row()] = value
        self.dataChanged.emit(index, index)
        return True
    
    def headerData(section, orientation, role = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return QString("Column %1").arg(section)
        else:
            return QString("Row %1").arg(section)
        
    def wantsUpdate(self):
        self.layoutChanged.emit()

    def deleteSelected(self):
        print "delete"
        assert len(self.selectionModel.selectedRows()) == 1
        row = self.selectionModel.selectedRows()[0]
        self.removeRow(row.row())
        if self.rowCount() > 0:
            self.selectionModel.select(self.index(0), QItemSelectionModel.Select)
        self.updateGUI()

    def moveSelectedUp(self):
        assert len(self.selectionModel.selectedRows()) == 1
        row = self.selectionModel.selectedRows()[0]
        if row.row() != 0:
            oldRow = row.row()
            newRow = oldRow - 1
            d = self.layerStack[oldRow]
            self.removeRow(oldRow)
            self.insertRow(newRow)
            self.setData(self.index(newRow), d)
            self.selectionModel.select(self.index(newRow), QItemSelectionModel.Select)
            self.orderChanged.emit()
            self.updateGUI()
    
    def moveSelectedDown(self):
        assert len(self.selectionModel.selectedRows()) == 1
        row = self.selectionModel.selectedRows()[0]
        if row.row() != self.rowCount() - 1:
            oldRow = row.row()
            newRow = oldRow + 1
            d = self.layerStack[oldRow]
            self.removeRow(oldRow)
            self.insertRow(newRow)
            self.setData(self.index(newRow), d)
            self.selectionModel.select(self.index(newRow), QItemSelectionModel.Select)
            self.orderChanged.emit()
            self.updateGUI()

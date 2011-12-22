from PyQt4.QtGui import QWidget,QGridLayout, QSizePolicy
from PyQt4.QtCore import Qt
from imageEditorComponents import PositionModelImage

class SynchronizedEditors(QWidget):
    
    def __init__(self):
        
        super(SynchronizedEditors,self).__init__()
        

        self._layout = QGridLayout()
        
        @property
        def layout(self):
            return self._layout
        @layout.setter
        def layout(self, layout):
            self._layout = layout
        self.initUI()
        
        
    def initUI(self):
        
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLayout(self._layout)
        self.show()
        
        
    def addEditorWidget(self,imageEditorWidget,position=(0,0)):
        
        self.checkPosition(position)
        self._layout.addWidget(imageEditorWidget,position[0],position[1])
        
        

        
    def checkPosition(self,position):
        
        widget = self._layout.itemAtPosition(position[0], position[1])
        if widget:
            freePos = self.getFreePosition()
            self._layout.removeItem(widget)
            self._layout.addItem(widget, freePos[0], freePos[1])
    
    def getFreePosition(self):
        i=0
        j=0
        while self._layout.itemAtPosition(i,j):
            while i > j:
                if self._layout.itemAtPosition(i,j):
                    break
                j=j+1
            i=i+1
        return (i,j)
    
    def link(self,iEWidget1,iEWidget2):
        iEWidget2._imageEditor.posModel = iEWidget1._imageEditor.posModel
        self._saveShape = iEWidget1._imageEditor.posModel.shape
    
    def unlink(self,iEWidget1,iEWidget2):
        shape = iEWidget1._imageEditor.posModel.shape
        iEWidget1._imageEditor.posModel = PositionModelImage()
        iEWidget2._imageEditor.posModel = PositionModelImage()
        iEWidget1._imageEditor.posModel.shape = shape
        iEWidget2._imageEditor.posModel.shape = shape
    
    
        
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import sys
    import signal   
    from PyQt4.QtGui import QApplication, QPushButton, QVBoxLayout
    from imageEditorWidget import TestWidget
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    
    app = QApplication(sys.argv)
    
    wrapper = QWidget()
    layout = QVBoxLayout()
    wrapper.setLayout(layout)

    synEditors = SynchronizedEditors()
    
    layout.addWidget(synEditors)
    
    test = TestWidget()
    iEWidget1 = test.makeWidget()
    iEWidget2 = test.makeWidget()
    iEWidget3 = test.makeWidget()
    
    button = QPushButton('Link')
    button.setCheckable(True)
    button.setChecked(False)
    
    def onLinkToggled(checked):
            if checked:
                synEditors.link(iEWidget1, iEWidget2)
            else:
                synEditors.unlink(iEWidget1, iEWidget2)                
    
    button.toggled.connect(onLinkToggled)
        
        
    layout.addWidget(button)
    
    
    synEditors.addEditorWidget(iEWidget1)
    synEditors.addEditorWidget(iEWidget2)

    wrapper.show()
    app.exec_()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import pyqtSignal, Qt, QPointF, QSize

from PyQt4.QtGui import QLabel, QPen, QPainter, QPixmap, QColor, QHBoxLayout, QVBoxLayout, \
                        QFont, QPainterPath, QBrush, QPolygonF, QSpinBox, QAbstractSpinBox, \
                        QCheckBox
import sys, random
import numpy, qimage2ndarray


class LabelButtons(QLabel):
    clicked = pyqtSignal()
    def __init__(self, backgroundColor, foregroundColor, width, height):
        QLabel.__init__(self)
        
        self.setColors(backgroundColor, foregroundColor)
        self.setPixmapSize(width, height)
        
    def setColors(self, backgroundColor, foregroundColor):
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor
        
    def setPixmapSize(self, width, height):
        self.pixmapWidth = width
        self.pixmapHeight = height
        
        
    def setUndockIcon(self):
        self.setToolTip("Undock")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawLine(70.0, 170.0, 190.0, 60.0)
        painter.drawLine(200.0, 140.0, 200.0, 50.0)
        painter.drawLine(110.0, 50.0, 200.0, 50.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setDockIcon(self):
        self.setToolTip("Dock")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawLine(70.0, 170.0, 190.0, 60.0)
        painter.drawLine(60.0, 90.0, 60.0, 180.0)
        painter.drawLine(150.0, 180.0, 60.0, 180.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setMaximizeIcon(self):
        self.setToolTip("Maximize")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawRect(50.0, 50.0, 150.0, 150.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setMinimizeIcon(self):
        self.setToolTip("Minimize")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawRect(50.0, 50.0, 150.0, 150.0)
        painter.drawLine(50.0, 125.0, 200.0, 125.0)
        painter.drawLine(125.0, 200.0, 125.0, 50.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setSpinBoxUpIcon(self):
        self.setToolTip("Up")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.foregroundColor)
        painter.setBrush(brush)
        pen = QPen(self.foregroundColor)
        painter.setPen(pen)
        points = QPolygonF()
        points.append(QPointF(125.0, 50.0))
        points.append(QPointF(200.0, 180.0))
        points.append(QPointF(125.0, 50.0))
        painter.drawPolygon(points)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setSpinBoxDownIcon(self):
        self.setToolTip("Down")
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(self.foregroundColor)
        painter.setBrush(brush)
        pen = QPen(self.foregroundColor)
        painter.setPen(pen)
        points = QPolygonF()
        points.append(QPointF(125.0, 200.0))
        points.append(QPointF(200.0, 70.0))
        points.append(QPointF(50.0, 70.0))
        
        
        #points  << QPointF(125.0, 200.0) << QPointF(200.0, 70.0) << QPointF(50.0, 70.0)
        painter.drawPolygon(points)
        painter.end()
        pixmap = pixmap.scaled(QSize(self.pixmapWidth, self.pixmapHeight),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def mouseReleaseEvent(self, event):
        if self.underMouse():
            self.clicked.emit()
            
class SpinBoxImageView(QHBoxLayout):
    valueChanged = pyqtSignal(int)
    def __init__(self, backgroundColor, foregroundColor, value, height, fontSize):
        QHBoxLayout.__init__(self)
        
        self.labelLayout = QVBoxLayout()
        self.upLabel = LabelButtons(backgroundColor, foregroundColor, height/2, height/2)
        self.labelLayout.addWidget(self.upLabel)
        self.upLabel.setSpinBoxUpIcon()
        self.upLabel.clicked.connect(self.on_upLabel)
        
        self.downLabel = LabelButtons(backgroundColor, foregroundColor, height/2, height/2)
        self.labelLayout.addWidget(self.downLabel)
        self.downLabel.setSpinBoxDownIcon()
        self.downLabel.clicked.connect(self.on_downLabel)
        
        self.addLayout(self.labelLayout)

        
        self.spinBox = QSpinBox()
        self.spinBox.valueChanged.connect(self.spinBoxValueChanged)
        self.addWidget(self.spinBox)
        self.spinBox.setToolTip("Spinbox")
        self.spinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinBox.setAlignment(Qt.AlignRight)
        self.spinBox.setMaximum(value)
        self.spinBox.setMaximumHeight(height)
        self.spinBox.setSuffix("/" + str(value))
        font = self.spinBox.font()
        font.setPixelSize(fontSize)
        self.spinBox.setFont(font)
        self.spinBox.setStyleSheet("QSpinBox { color: " + str(foregroundColor.name()) + "; font: bold; background-color: " + str(backgroundColor.name()) + "; border:0;}")
    
    def spinBoxValueChanged(self, value):
        self.valueChanged.emit(value)    
    
    def setValue(self, value):
        self.spinBox.setValue(value)
    
    def setNewValue(self, value):
        self.spinBox.setMaximum(value)
        self.spinBox.setSuffix("/" + str(value))
        
    def on_upLabel(self):
        self.spinBox.setValue(self.spinBox.value() + 1)
        
    def on_downLabel(self):
        self.spinBox.setValue(self.spinBox.value() - 1)
        
            
class imageView2DHud(QHBoxLayout):
#    valueChanged = pyqtSignal(int)
    dockButtonClicked = pyqtSignal()
    maximizeButtonClicked = pyqtSignal()
    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)
        
    def createImageView2DHud(self, axis, value, backgroundColor, foregroundColor):
        width = 20
        height = 20 
        
        self.addSpacing(4)
        self.axisLabel = QLabel()
        self.axisLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        pixmap = QPixmap(250, 250)
        pixmap.fill(backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(250-30)
        path = QPainterPath()
        path.addText(QPointF(50, 250-50), font, axis)
        brush = QBrush(foregroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(width,height),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.axisLabel.setPixmap(pixmap)  
        self.addWidget(self.axisLabel)
        
        self.sliceSelector = SpinBoxImageView(backgroundColor, foregroundColor, value, height, 12)
#        self.sliceSelector.valueChanged.connect(self.spinBoxChanged)
        self.addSpacing(4)
        self.addLayout(self.sliceSelector)
      
        self.addStretch()
        
        self.dockButton = LabelButtons(backgroundColor, foregroundColor, width, height)
        self.dockButton.clicked.connect(self.on_dockButton)
        self.dockButton.setUndockIcon()
        self.addWidget(self.dockButton)
        
        self.addSpacing(4)
        
        self.maxButton = LabelButtons(backgroundColor, foregroundColor, width, height)
        self.maxButton.clicked.connect(self.on_maxButton)
        self.maxButton.setMaximizeIcon()
        self.addWidget(self.maxButton)
        self.addSpacing(4)
    
#    def spinBoxChanged(self, value):
#        self.valueChanged.emit(value)
        
    def on_dockButton(self):
        self.dockButtonClicked.emit()
    
        
    def on_maxButton(self):
        self.maximizeButtonClicked.emit()
        
            
class QuadStatusBar(QHBoxLayout):
    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)   
        
    def createQuadViewStatusBar(self, xbackgroundColor, xforegroundColor, ybackgroundColor, yforegroundColor, zbackgroundColor, zforegroundColor, graybackgroundColor, grayforegroundColor):             
        
        self.xLabel = QLabel()
        self.xLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.xLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(xbackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(xforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "X")
        brush = QBrush(xforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.xLabel.setPixmap(pixmap)
        self.xSpinBox = QSpinBox()
        self.xSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.xSpinBox.setEnabled(False)
        self.xSpinBox.setAlignment(Qt.AlignCenter)
        self.xSpinBox.setToolTip("xSpinBox")
        self.xSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.xSpinBox.setMaximumHeight(20)
        self.xSpinBox.setMaximum(9999)
        font = self.xSpinBox.font()
        font.setPixelSize(14)
        self.xSpinBox.setFont(font)
        self.xSpinBox.setStyleSheet("QSpinBox { color: " + str(xforegroundColor.name()) + "; font: bold; background-color: " + str(xbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.xSpinBox)
        
        self.yLabel = QLabel()
        self.yLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.yLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(ybackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(yforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Y")
        brush = QBrush(yforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.yLabel.setPixmap(pixmap)
        self.ySpinBox = QSpinBox()
        self.ySpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ySpinBox.setEnabled(False)
        self.ySpinBox.setAlignment(Qt.AlignCenter)
        self.ySpinBox.setToolTip("ySpinBox")
        self.ySpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.ySpinBox.setMaximumHeight(20)
        self.ySpinBox.setMaximum(9999)
        font = self.ySpinBox.font()
        font.setPixelSize(14)
        self.ySpinBox.setFont(font)
        self.ySpinBox.setStyleSheet("QSpinBox { color: " + str(yforegroundColor.name()) + "; font: bold; background-color: " + str(ybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.ySpinBox)
        
        self.zLabel = QLabel()
        self.zLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.zLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(zbackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(zforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Z")
        brush = QBrush(zforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.zLabel.setPixmap(pixmap)
        self.zSpinBox = QSpinBox()
        self.zSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.zSpinBox.setEnabled(False)
        self.zSpinBox.setAlignment(Qt.AlignCenter)
        self.zSpinBox.setToolTip("zSpinBox")
        self.zSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.zSpinBox.setMaximumHeight(20)
        self.zSpinBox.setMaximum(9999)
        font = self.zSpinBox.font()
        font.setPixelSize(14)
        self.zSpinBox.setFont(font)
        self.zSpinBox.setStyleSheet("QSpinBox { color: " + str(zforegroundColor.name()) + "; font: bold; background-color: " + str(zbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.zSpinBox)
        
        self.addSpacing(4)
        
        self.grayScaleLabel = QLabel()
        self.grayScaleLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.grayScaleLabel)
        pixmap = QPixmap(610, 250)
        pixmap.fill(graybackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(grayforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Gray")
        brush = QBrush(grayforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(61,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.grayScaleLabel.setPixmap(pixmap)
        self.grayScaleSpinBox = QSpinBox()
        self.grayScaleSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.grayScaleSpinBox.setEnabled(False)
        self.grayScaleSpinBox.setAlignment(Qt.AlignCenter)
        self.grayScaleSpinBox.setToolTip("grayscaleSpinBox")
        self.grayScaleSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.grayScaleSpinBox.setMaximum(255)
        self.grayScaleSpinBox.setMaximumHeight(20)
        self.grayScaleSpinBox.setMaximum(255)
        font = self.grayScaleSpinBox.font()
        font.setPixelSize(14)
        self.grayScaleSpinBox.setFont(font)
        self.grayScaleSpinBox.setStyleSheet("QSpinBox { color: " + str(grayforegroundColor.name()) + "; font: bold; background-color: " + str(graybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.grayScaleSpinBox)
        
        self.addStretch()
        
        self.positionCheckBox = QCheckBox()
        self.positionCheckBox.setChecked(True)
        self.positionCheckBox.setCheckable(True)
        self.positionCheckBox.setText("Position")
        self.addWidget(self.positionCheckBox)
        
        self.addSpacing(20)
        
        self.channelLabel = QLabel("Channel:")
        self.addWidget(self.channelLabel)
        
        self.channelSpinBox = QSpinBox()
        self.addWidget(self.channelSpinBox)
        self.addSpacing(20)
        
        self.timeLabel = QLabel("Time:")
        self.addWidget(self.timeLabel)
        
        self.timeSpinBox = QSpinBox()
        self.addWidget(self.timeSpinBox)
        
    def setGrayScale(self, gray):
        self.grayScaleSpinBox.setValue(gray)
        
    def setMouseCoords(self, x, y, z):
        self.xSpinBox.setValue(x)
        self.ySpinBox.setValue(y)
        self.zSpinBox.setValue(z)
        
        
if __name__ == "__main__":
    from PyQt4.QtGui import QDialog, QApplication
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    widget = QDialog()
    ex1 = imageView2DHud()
    ex1.createImageView2DHud("X", 12, QColor("red"), QColor("white"))
    widget.setLayout(ex1)
    widget.show()
    widget.raise_()
    app.exec_()
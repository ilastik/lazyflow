#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtCore import QRect, QPoint, Qt, QTimer
from PyQt4.QtGui import QApplication, QPainter, QImage, QBrush, QPen, QColor, \
                        QBrush

import sys
import qimage2ndarray, numpy
import h5py

app = QApplication(sys.argv)

def sliceImg(width, height, axisLabels, perpAxisLabel, perpAxisValue):
    print perpAxisLabel, perpAxisValue
    img = QImage(width, height, QImage.Format_ARGB32)
    img.fill(0)

    p = QPainter(img)
    p.setPen(QColor(255,255,255))
    p.setBrush(QBrush(QColor(255,255,255)))
    def arrow(p, From, To, label):
        p.drawLine(From, To)
        p.drawText(To, label)

    offset = 10
    arrow(p, QPoint(offset, offset), QPoint(offset, height-offset), axisLabels[1])
    arrow(p, QPoint(offset, offset), QPoint(width-offset,  offset), axisLabels[0])
    p.drawText(2*offset, 2*offset, "%s=%d" % (perpAxisLabel, perpAxisValue))
    fm = p.fontMetrics()
    size = fm.size(Qt.TextSingleLine, "updown")

    p.drawText(numpy.random.randint(offset, width-offset-size.width()), numpy.random.randint(offset, height-offset-size.height()), "updown")

    dots = []
    numPixels = 0
    while numPixels < 30:
        r = numpy.random.randint(1, 255)
        rx, ry = numpy.random.randint(offset, width-offset), numpy.random.randint(offset, height-offset)
        if img.pixel(rx,ry) != 0:
            continue
        p.setPen(QPen(QColor(r,r,r)))
        p.drawPoint(rx, ry)
        dots.append(((rx,ry), r))
        numPixels += 1

    p.end()
    
    
    img.save('test.png')

    a = qimage2ndarray.rgb_view(img)
    a = a[:,:,0].squeeze().swapaxes(0,1)

    for (rx,ry), r in dots:
        assert QColor.fromRgba(img.pixel(rx,ry)).red() == r, "QColor.fromRgba(img.pixel(rx,ry)).red() == %d != %d" % (QColor.fromRgba(img.pixel(rx,ry)).red(), r)
        assert(a[rx,ry] == r), "a[%d,%d] == %d != %d)" % (rx, ry, a[rx,ry], r)
    return (a, dots)

shape = (90,110,120)
array3d = numpy.zeros(shape)

for z in range(0,shape[2], 10):
    a, dots = sliceImg(shape[0], shape[1], ('x', 'y'), 'z', z)
    array3d[:,:,z] = a
    for (rx,ry), r in dots:
        assert array3d[rx,ry,z] == r
for y in [0,]+range(3,shape[1], 10):
    a, dots = sliceImg(shape[0], shape[2], ('x', 'z'), 'y', y)
    array3d[:,y,:] = a
    for (rx,ry), r in dots:
        assert array3d[rx,y,ry] == r
for x in [0,]+range(6,shape[0], 10):
    a, dots = sliceImg(shape[1], shape[2], ('y', 'z'), 'x', x)
    array3d[x,:,:] = a
    for (rx,ry), r in dots:
        assert array3d[x,rx,ry] == r

shape5d =  (1,)+shape+(1,)
array5d = array3d.reshape(shape5d)

f=h5py.File("l.h5", 'w')
f.create_group("volume")
f.create_dataset("volume/data", shape5d, data=array5d.astype(numpy.uint8))
f.close()

#QTimer.singleShot(0, app.quit)
#app.exec_()
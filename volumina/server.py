#!/usr/bin/python

# The VoluminaTileServer is a proof-of-concept demonstrating how to
# serve tiles to be consumed and displayed by CATMAID

# Requirements:
# sudo pip install tornado

from PyQt4.QtCore import QRect, QIODevice, QBuffer

import tornado.ioloop
import tornado.web
import numpy as np

def qimage2str( qimg, format = 'PNG' ):
    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    qimg.save(buffer, format)
    data = buffer.data() # type(data) == QByteArray
    buffer.close()    
    # extracts Python str from QByteArray    
    return data.data()



class TileHandler(tornado.web.RequestHandler):
	def initialize(self, imageSource, sliceSource, shape):
            self.ims = imageSource
            self.sls = sliceSource
            self.shape = shape
		
	def get(self):
            #
            # parse the arguments
            #
            axistag_map = {'t': 0, 'x': 1, 'y': 2, 'z': 3, 'c': 4}

            pos = []
            pos.append(int(self.get_argument('t', default = '0')))
            pos.append(int(self.get_argument('x', default = '0')))
            pos.append(int(self.get_argument('y', default = '0')))
            pos.append(int(self.get_argument('z', default = '0')))
            pos.append(int(self.get_argument('c', default = '0')))

            row_axis = axistag_map[self.get_argument('row', default = 'y')]
            col_axis = axistag_map[self.get_argument('col', default = 'x')]

            width=int(self.get_argument('width', default = (self.shape[col_axis] - pos[col_axis])))
            height=int(self.get_argument('height', default = (self.shape[row_axis] - pos[row_axis])))
		
            scale = float(self.get_argument('scale', default=1))

            #
            # render tile
            #
            through_axes = [0,1,2,3,4]
            through_axes.remove(row_axis)
            through_axes.remove(col_axis)
            through = [pos[i] for i in through_axes]
            self.sls.through = through

            qimg = self.ims.request(QRect(pos[col_axis], pos[row_axis], width, height)).wait()
            zoomed_width = int(width * scale)
            qimg = qimg.scaledToWidth(zoomed_width)

            #
            # send tile
            #
            self.set_header('Content-Type', 'image/png') 
            self.write(qimage2str(qimg))
            self.flush()


class Server( object ):
    def __init__( self, ims, sls, shape, port=8888 ):
        assert(len(shape) == 5)
        self.port = port
        self._app = tornado.web.Application([
		    (r"/", TileHandler, {'imageSource': ims, 'sliceSource': sls, 'shape': shape}),
		    ])
    
    def start( self ):
        self._app.listen( self.port )
	tornado.ioloop.IOLoop.instance().start()
        
	

if __name__ == "__main__":
    import numpy as np
    from pixelpipeline.datasources import ArraySource
    from volumina.layer import GrayscaleLayer
    from volumina.stackEditor import StackEditor
    from scipy.misc import lena
    
    data = np.load("_testing/5d.npy")
    #data = np.random.random_integers(0,255, size= (2362,994,47))
    #data = lena()
    #data = data[np.newaxis, ..., np.newaxis]
    ds = ArraySource(data)
    
    se = StackEditor()
    se.layerStackModel.append(GrayscaleLayer(ds))

    ims = se.imagePump.stackedImageSources.getImageSource(0)
    tileServer = Server( ims, se.imagePump.syncedSliceSources, data.shape, port=8080)
    tileServer.start()


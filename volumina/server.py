#!/usr/bin/python

# The VoluminaTileServer is a proof-of-concept demonstrating how to
# serve tiles to be consumed and displayed by CATMAID

# Requirements:
# sudo pip install tornado

from PyQt4.QtCore import QRect, QIODevice, QBuffer

import tornado.ioloop
import tornado.web
import tornado.escape
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


class MetadataHandler(tornado.web.RequestHandler):
    
    def get(self):
        # need to parse project_id and stack_id from CATMAID ?
        result={
            'sid': 1,
            'pid': 1,
            'ptitle': 'Project Title',
            'stitle': 'Stack Title',
            'min_zoom_level': -1,
            'file_extension': 'png',
            'editable': 1, # TODO: needs fix
            'translation': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0
            }, # TODO: use project_stack
            'resolution': {
                'x': 1.0,
                'y': 1.0,
                'z': 1.0
            },
            'dimension': {
                'x': 512,
                'y': 512,
                'z': 10
            },
            'tile_height': 256,
            'tile_width': 256,
            'tile_source_type': 2,
            'broken_slices': {},
            'trakem2_project': 0,
            'overlay': {
            '0': {
                    'title': 'Segmentation result',
                    # would map to url where corresponding tiles are served
                    'image_base': 'http://localhost:8080/',
                    'default_opacity': 100,
                    'file_extension': 'png'
                }
            }, # the overlays define layers
            
            # number of scale levels
            # additional fields special for tileserver
            'image_base': 'http://localhost:8080/', # tile source base url
            'labelupload_url': 'http://localhost:8080/labelupload'
        }
        self.write(tornado.escape.json_encode(result))

class Server( object ):
    def __init__( self, ims, sls, shape, port=8888 ):
        assert(len(shape) == 5)
        self.port = port
        self._app = tornado.web.Application([
		    (r"/", TileHandler, {'imageSource': ims, 'sliceSource': sls, 'shape': shape}),
            (r"/metadata", MetadataHandler),
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
    
    #data = np.load("_testing/5d.npy")
    data = np.random.random_integers(0,255, size= (512,512,10))
    #data = lena()
    data = data[np.newaxis, ..., np.newaxis]
    ds = ArraySource(data)
    
    se = StackEditor()
    se.layerStackModel.append(GrayscaleLayer(ds))

    ims = se.imagePump.stackedImageSources.getImageSource(0)
    tileServer = Server( ims, se.imagePump.syncedSliceSources, data.shape, port=8080)
    tileServer.start()


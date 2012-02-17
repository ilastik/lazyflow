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
	def initialize(self, imageSource, sliceSource, posModel, shape):
            self.ims = imageSource
            self.sls = sliceSource
            self.posModel = posModel
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

            max_width = self.shape[col_axis] - pos[col_axis]
            max_height = self.shape[row_axis] - pos[row_axis]
            width=int(self.get_argument('width', default = max_width))
            height=int(self.get_argument('height', default = max_height))

            width = width if width <= max_width else max_width
            height = height if height <= max_height else max_height
		
            scale = float(self.get_argument('scale', default=1))

            #
            # render tile
            #
            through_axes = [0,1,2,3,4]
            through_axes.remove(row_axis)
            through_axes.remove(col_axis)
            through = [pos[i] for i in through_axes]
            self.sls.through = through
            #slPos = list(self.posModel.slicingPos)
            #slPos[2] = pos[3]
            #self.posModel.slicingPos = slPos

            qimg = self.ims.request(QRect(pos[col_axis], pos[row_axis], height, width)).wait()
            zoomed_width = int(width * scale)
            qimg = qimg.scaledToWidth(zoomed_width)

            #
            # send tile
            #
            self.set_header('Content-Type', 'image/png') 
            self.write(qimage2str(qimg))
            self.flush()


class MetadataHandler(tornado.web.RequestHandler):
    def initialize( self, server ):
        self.server = server

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
                'x': self.server.shape[1],
                'y': self.server.shape[2],
                'z': self.server.shape[3]
            },
            'tile_height': 256,
            'tile_width': 256,
            'tile_source_type': 2,
            'broken_slices': {},
            'trakem2_project': 0,
            'overlay': {
            '0': {
                    'title': 'Overlay 0',
                    # would map to url where corresponding tiles are served
                    'image_base': 'http://localhost:%d/overlay0' % self.server.port,
                    'default_opacity': 100,
                    'file_extension': 'png'
                },
            '1': {
                    'title': 'Overlay 1',
                    # would map to url where corresponding tiles are served
                    'image_base': 'http://localhost:%d/overlay1' % self.server.port,
                    'default_opacity': 100,
                    'file_extension': 'png'
                },
            '2': {
                    'title': 'Overlay 2',
                    # would map to url where corresponding tiles are served
                    'image_base': 'http://localhost:%d/overlay2' % self.server.port,
                    'default_opacity': 100,
                    'file_extension': 'png'
                }
            }, # the overlays define layers
            
            # number of scale levels
            # additional fields special for tileserver
            'image_base': 'http://localhost:%d/' % self.server.port, # tile source base url
            'labelupload_url': 'http://localhost:%d/labelupload' % self.server.port
        }
        self.write(tornado.escape.json_encode(result))

class CatmaidServer( object ):
    def __init__( self, ims, sls, posModel, shape, port=8888 ):
        assert(len(shape) == 5), shape
        self.port = port
        self.shape = shape
        self._app = tornado.web.Application([
                (r"/", TileHandler, {'imageSource': ims[3], 'sliceSource': sls, 'posModel': posModel, 'shape': shape}),
                (r"/overlay0", TileHandler, {'imageSource': ims[1], 'sliceSource': sls, 'posModel': posModel, 'shape': shape}),
                (r"/overlay1", TileHandler, {'imageSource': ims[2], 'sliceSource': sls, 'posModel': posModel, 'shape': shape}),
                (r"/overlay2", TileHandler, {'imageSource': ims[0], 'sliceSource': sls, 'posModel': posModel, 'shape': shape}),
                (r"/metadata", MetadataHandler, {'server': self}),
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
    #data = np.random.random_integers(0,255, size= (512,512,10))
    #data = lena()
    #data = data[np.newaxis, ..., np.newaxis]
    ds = ArraySource(data)
    
    se = StackEditor()
    se.layerStackModel.append(GrayscaleLayer(ds))

    ims = se.imagePump.stackedImageSources.getImageSource(0)
    tileServer = CatmaidServer( [ims, ims], se.imagePump.syncedSliceSources, None, data.shape, port=8080)
    tileServer.start()


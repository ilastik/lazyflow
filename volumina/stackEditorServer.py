#!/usr/bin/python

# The VoluminaTileServer is a proof-of-concept demonstrating how to
# serve tiles to be consumed and displayed by CATMAID

# Requirements:
# sudo pip install tornado

from PyQt4.QtCore import QRect, QIODevice, QBuffer

import tornado.ioloop
import tornado.web
import numpy as np
import tornado.escape

def qimage2str( qimg, format = 'PNG' ):
    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    qimg.save(buffer, format)
    data = buffer.data() # type(data) == QByteArray
    buffer.close()    
    # extracts Python str from QByteArray    
    return data.data()


# This handler serves tiles from e.g. volumina
class TileHandler(tornado.web.RequestHandler):
	
	def initialize(self, imageSource):
            self._ims = imageSource
		
	def get(self):
		print "the get request", self.request
		
		# parse the arguments
		# the usable parameters posted are:
		# x, y, dx : tileWidth, dy : tileHeight,
		# scale : scale, // defined as 1/2**zoomlevel
		# z : z
		# everything in bitmap pixel coordinates
		x=int(self.get_argument('x', default = '0'))
		y=int(self.get_argument('y', default = '0'))
		z=int(self.get_argument('z', default = '0'))

		dx=int(self.get_argument('dx', default = '256'))
		dy=int(self.get_argument('dy', default = '256'))
		
		scale = float(self.get_argument('scale', default='1'))

		qimg = self._ims.request(QRect(x,y, dx, dy)).wait()
		zoomed_width = int(dx * scale)
		qimg = qimg.scaledToWidth(zoomed_width)

		self.set_header('Content-Type', 'image/png') 
		self.write(qimage2str(qimg))
		self.flush()
        
	def post(self):
		print "the post request", self.request
		self.write("hello post")

# This handler manages POST request from the canvas label painting
class LabelUploader(tornado.web.RequestHandler):
	
	def post(self):
		datauri = self.get_argument('data')[0]
		output = open('output.png', 'wb')
		output.write(datauri.decode('base64'))
		output.close()
		self.write("success")
	
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
                'x': 5120,
                'y': 5120,
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
                    'image_base': 'http://localhost:8888/',
                    'default_opacity': 50,
                    'file_extension': 'png'
                }
            }, # the overlays define layers
            
            # number of scale levels
            # additional fields special for tileserver
            'image_base': 'http://localhost:8888/', # tile source base url
            'labelupload_url': 'http://localhost:8888/labelupload'
        }
        self.write(tornado.escape.json_encode(result))
        
        
class C5ifyer(object):
    def __init__(self, array3d):
        self.a = array3d
        self.shape = (1,) + array3d.shape + (1,)
            
    def __getitem__( self, arg ):
        req = self.a[arg[1:4]]
        return req[np.newaxis, ..., np.newaxis]

if __name__ == "__main__":
    import numpy as np
    from pixelpipeline.datasources import ArraySource
    from volumina.layer import GrayscaleLayer
    from volumina.stackEditor import StackEditor
    from scipy.misc import lena
    import h5py
    f = h5py.File("/home/stephan/dev/CATMAID/django/hdf5/fibdata.hdf", 'r')
    data = C5ifyer(f['data'])
    #data = np.random.random_integers(0,255, size= (512,512,128))
    #data = lena()
    #data = data[np.newaxis, ..., np.newaxis, np.newaxis]
    ds = ArraySource(data)
    
    se = StackEditor()
    se.layerStackModel.append(GrayscaleLayer(ds))

    VoluminaTileServer = tornado.web.Application([
		    (r"/", TileHandler, {'imageSource': se.imagePump.stackedImageSources.getImageSource(0)}),
		    (r"/labelupload", LabelUploader),
            (r"/metadata", MetadataHandler),
		    ])


    VoluminaTileServer.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

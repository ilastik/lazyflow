#!/usr/bin/python

# The VoluminaTileServer is a proof-of-concept demonstrating how to
# serve tiles to be consumed and displayed by CATMAID

# Requirements:
# sudo pip install tornado

import tornado.ioloop
import tornado.web

import Image
import cStringIO 
import numpy as np

# This handler serves tiles from e.g. volumina
class TileHandler(tornado.web.RequestHandler):
	
	def initialize(self, database):
		self.database = database
		
	def get(self):
		print "the get request", self.request
		
		# parse the arguments
		#z=self.get_argument('z')
        # the usable parameters posted are:
        # x, y, dx : tileWidth, dy : tileHeight,
        # scale : scale, // defined as 1/2**zoomlevel
        # z : z
        # everything in bitmap pixel coordinates
		
		# create an example PNG
		w,h=256,256
		img = np.empty((w,h),np.uint32)
		img.shape=h,w
		img[0,0]=0x800000FF
		img[:100,:100]=0xFFFF0000
		pilImage = Image.frombuffer('RGBA',(w,h),img,'raw','RGBA',0,1)
		imgbuff = cStringIO.StringIO() 
		pilImage.save(imgbuff, format='PNG') 
		imgbuff.seek(0)
		self.set_header('Content-Type', 'image/png') 
		self.write(imgbuff.read()) 
		imgbuff.close()
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
	

VoluminaTileServer = tornado.web.Application([
    (r"/", TileHandler, dict(database="123")),
    (r"/labelupload", LabelUploader),
])

if __name__ == "__main__":
    VoluminaTileServer.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

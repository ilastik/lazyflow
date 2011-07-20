import numpy, vigra

class DataAccessor():
    """
    This class gives consistent access to _data volumes, images channels etc.
    access is always of the form [time, x, y, z, channel]
    """
    
    def __init__(self, data, channels = False,  autoRgb = True):
        """
        _data should be a numpy/vigra array that transformed to the [time, x, y, z, channel] access like this:
            1d: (a,b), b != 3 and channels = False  (0,0,a,b,0)
            1d: (a,b), b == 3 or channels = True:  (0,0,0,a,b)
            2d: (a,b,c), c != 3 and channels = False:  (0,a,b,c,0)
            2d: (a,b,c), c == 3 or channels = True:  (0,0,a,b,c)
            etc.
        """
        
        if issubclass(data.__class__,  DataAccessor):
            self._data = data._data
            self.rgb = data.rgb
            self.shape = data.shape
            self.dtype = data.dtype
        else:

            if len(data.shape) == 5:
                channels = True
                
            if issubclass(data.__class__, DataAccessor):
                data = data._data
                channels = True
            
            rgb = 1
            if data.shape[-1] == 3 or channels:
                rgb = 0

            tempShape = data.shape

            self._data = data
            
            if hasattr(vigra.arraytypes, 'VigraArray'):
                # Vigra with axistags
                vigraArrayClass = vigra.arraytypes.VigraArray
            elif hasattr(vigra.arraytypes, '_VigraArray'):
                # Vigra without axistags
                vigraArrayClass = vigra.arraytypes._VigraArray
            else:
                raise RuntimeError('Vigra version does not have an VigraArray class.')

            if issubclass(data.__class__, vigraArrayClass):
                for i in range(len(data.shape)/2):
                    #self._data = self._data.swapaxes(i,len(_data.shape)-i)
                    pass
                self._data = self._data.view(numpy.ndarray)
                #self._data.reshape(tempShape)


            for i in range(5 - (len(data.shape) + rgb)):
                tempShape = (1,) + tempShape
                
            if rgb:
                tempShape = tempShape + (1,)
            
            if len(self._data.shape) != 5:
                self._data = self._data.reshape(tempShape)
                
            self.channels = self._data.shape[-1]

            self.rgb = False
            if autoRgb:
                if data.shape[-1] == 3:
                    self.rgb = True

            self.shape = self._data.shape
            self.dtype = self._data.dtype


    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, data):
        self._data[key] = data

    def getSlice(self, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                return self._data[time, num, :,: , :]
            elif axis == 1:
                return self._data[time, :,num,: , :]
            elif axis ==2:
                return self._data[time, :,: ,num,  :]
        else:
            if axis == 0:
                return self._data[time, num, :,: , channel]
            elif axis == 1:
                return self._data[time, :,num,: , channel]
            elif axis ==2:
                return self._data[time, :,: ,num,  channel]
            

    def setSlice(self, data, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                self._data[time, num, :,: , :] = data
            elif axis == 1:
                self._data[time, :,num,: , :] = data
            elif axis ==2:
                self._data[time, :,: ,num,  :] = data
        else:        
            if axis == 0:
                self._data[time, num, :,: , channel] = data
            elif axis == 1:
                self._data[time, :,num,: , channel] = data
            elif axis ==2:
                self._data[time, :,: ,num,  channel] = data

    def getSubSlice(self, offsets, sizes, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+sizes[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+sizes[1]

        if self.rgb is True:
            if axis == 0:
                return self._data[time, num, ax0l:ax0r,ax1l:ax1r , :]
            elif axis == 1:
                return self._data[time, ax0l:ax0r, num,ax1l:ax1r , :]
            elif axis ==2:
                return self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  :]
        else:
            if axis == 0:
                return self._data[time, num, ax0l:ax0r,ax1l:ax1r , channel]
            elif axis == 1:
                return self._data[time, ax0l:ax0r, num,ax1l:ax1r , channel]
            elif axis ==2:
                return self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel]
            

    def setSubSlice(self, offsets, data, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+data.shape[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+data.shape[1]

        if self.rgb is True:
            if axis == 0:
                self._data[time, num,  ax0l:ax0r, ax1l:ax1r , :] = data
            elif axis == 1:
                self._data[time, ax0l:ax0r,num, ax1l:ax1r , :] = data
            elif axis ==2:
                self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  :] = data
        else:
            if axis == 0:
                self._data[time, num,  ax0l:ax0r, ax1l:ax1r , channel] = data
            elif axis == 1:
                self._data[time, ax0l:ax0r,num, ax1l:ax1r , channel] = data
            elif axis ==2:
                self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel] = data

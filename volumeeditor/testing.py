import scipy, numpy

def meshgrid2(*arrs):
    #This function is copied from:
    #http://stackoverflow.com/questions/1827489/numpy-meshgrid-in-3d
    arrs = tuple(reversed(arrs))
    lens = map(len, arrs)
    dim = len(arrs)
    sz = 1
    for s in lens:
        sz*=s
    ans = []    
    for i, arr in enumerate(arrs):
        slc = [1]*dim
        slc[i] = lens[i]
        arr2 = numpy.asarray(arr).reshape(slc)
        for j, sz in enumerate(lens):
            if j!=i:
                arr2 = arr2.repeat(sz, axis=j) 
        ans.append(arr2)
    return tuple(ans)

def testVolume(N = 40):
    """generates viewable 3D data"""
    N2 = N/2
    X,Y,Z = meshgrid2(numpy.arange(N),numpy.arange(N),numpy.arange(N))
    s = (numpy.random.rand(N,N,N)*255).astype(numpy.uint8)
    center = numpy.asarray((N2,N2,N2))
    s[(X-10)**2+(Y-10)**2+(Z-15)**2 < (N2-2)**2] = 0
    s[(X-30)**2+(Y-30)**2+(Z-30)**2 < (10)**2] = 128
    s[0:10,0:10,0:10] = 200
    return s

class AnnotatedImageData():
    """
    Helper class to encapsulate the overlay slice and its drawing related settings
    for passing it around, mostly used in the volumeEditor (->move there ?)
    """
    def __init__(self, data, color, alpha, colorTable, min = None, max = None, autoAlphaChannel = True):
        assert(type(data) == numpy.ndarray)
        self.colorTable = colorTable
        self.color = color
        self.alpha = alpha
        self.alphaChannel = None
        self.autoAlphaChannel = autoAlphaChannel
        self._data = data
        self.min = min
        self.max = max
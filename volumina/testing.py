import numpy

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
    """generates viewable 3D data embedded in 5D"""
    N2 = N/2
    X,Y,Z = meshgrid2(numpy.arange(N),numpy.arange(N),numpy.arange(N))
    s = (numpy.random.rand(1,N,N,N,1)*255).astype(numpy.uint8)
    s[0,(X-10)**2+(Y-10)**2+(Z-15)**2 < (N2-2)**2,0] = 0
    s[0,(X-30)**2+(Y-30)**2+(Z-30)**2 < (10)**2,0] = 128
    s[0,0:10,0:10,0:10,0] = 200
    return s

def TwoDtestVolume(N = 40):
    """generates viewable 2D data embedded in 5D"""
    N2 = N/2
    X,Y,Z = meshgrid2(numpy.arange(N),numpy.arange(N),numpy.arange(N))
    s = (numpy.random.rand(1,N,N,N,1)*255).astype(numpy.uint8)
    s[0,(X-10)**2+(Y-10)**2+(Z-15)**2 < (N2-2)**2,0] = 0
    s[0,(X-30)**2+(Y-30)**2+(Z-30)**2 < (10)**2,0] = 128
    s[0,0:10,0:10,0:10,0] = 200
    s=s[0,:,:,(N/2),0]
    return s




def stripes(X = 8, Y = 8, Z = 8):
    """generates 3D Data with black and white stripes to check cursor positions"""
    array = numpy.arange(X*Y*Z).reshape(1,X,Y,Z,1).astype(numpy.uint8)
    
    for x in range(X):
        for y in range(Y):
            for z in range(Z):
                if z % 2 == 0:
                    array[x,y,z] = 200
                else:
                    array[x,y,z] = 0
    
    #array.astype(numpy.uint8)
    return array    

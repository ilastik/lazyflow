try:
    from vtk import vtkPropAssembly, vtkImplicitPlaneRepresentation, vtkPolyData, vtkPoints, \
                vtkCellArray, vtkImplicitPlaneWidget2, vtkTubeFilter, vtkPolyDataMapper, \
                vtkActor, vtkPlane

except:
    print 'Vtk not found in slicingPlanesWidget'
    vtkfound = 'false'

#*******************************************************************************
# S l i c i n g P l a n e s W i d g e t                                        *
#*******************************************************************************

class SlicingPlanesWidget(vtkPropAssembly):
    def SetPickable(self, pickable):
        props = self.GetParts()
        props.InitTraversal();
        for i in range(props.GetNumberOfItems()):
            props.GetNextProp().SetPickable(pickable)
    
    def __init__(self, dataShape, interactor):
        self.dataShape = dataShape
        self.planes = []
        self.coordinate = [0,0,0]
        self.lastChangedAxis = -1
        for i in range(3):
            p = vtkImplicitPlaneRepresentation()
            p.SetPlaceFactor(1.0)
            p.OutsideBoundsOn()
            p.ScaleEnabledOff()
            p.SetOrigin(0.25,0.25,0.25)
            p.PlaceWidget([0.1,dataShape[0],0.1,dataShape[1],0.1,dataShape[2]])
            if i==0:
                p.SetNormal(1,0,0)
                p.GetSelectedPlaneProperty().SetColor(1,0,0)
                p.GetEdgesProperty().SetColor(1,0,0) #bug in VTK
            elif i==1:
                p.SetNormal(0,1,0)
                p.GetSelectedPlaneProperty().SetColor(0,1,0)
                p.GetEdgesProperty().SetColor(0,1,0) #bug in VTK
            else: 
                p.SetNormal(0,0,1)
                p.GetSelectedPlaneProperty().SetColor(0,0,1)
                p.GetEdgesProperty().SetColor(0,0,1) #bug in VTK
            p.GetPlaneProperty().SetOpacity(0.001)
            #do not draw outline
            p.GetOutlineProperty().SetColor(0,0,0)
            p.GetOutlineProperty().SetOpacity(0.0)
            #do not draw normal
            p.GetSelectedNormalProperty().SetOpacity(0.0)
            p.GetNormalProperty().SetOpacity(0.0)
            p.OutlineTranslationOff()
            p.TubingOff()
            
            self.cross = vtkPolyData()
            points = vtkPoints()
            polys = vtkCellArray()
            points.SetNumberOfPoints(6)
            for i in range(3):
                polys.InsertNextCell(2)
                polys.InsertCellPoint(2*i); polys.InsertCellPoint(2*i+1)
            self.cross.SetPoints(points)
            self.cross.SetLines(polys)
            
            pw = vtkImplicitPlaneWidget2()
            pw.SetRepresentation(p)
            pw.SetInteractor(interactor)
            pw.AddObserver("InteractionEvent", self.__PlanePositionCallback)
            
            self.planes.append(pw)
            
        tubes = vtkTubeFilter()
        tubes.SetNumberOfSides(16)
        tubes.SetInput(self.cross)
        tubes.SetRadius(1.0)
        
        crossMapper = vtkPolyDataMapper()
        crossMapper.SetInput(self.cross)
        crossActor = vtkActor()
        crossActor.SetMapper(crossMapper)
        crossActor.GetProperty().SetColor(0,0,0)
        self.AddPart(crossActor)
        
        #initially invoke the event!
        self.InvokeEvent("CoordinatesEvent")
    
    def Plane(self, axis):
        p = vtkPlane()
        self.planes[axis].GetRepresentation().GetPlane(p)
        return p
    def PlaneX(self):
        return self.Plane(0)
    def PlaneY(self):
        return self.Plane(1)
    def PlaneZ(self):
        return self.Plane(2)
        
    def ShowPlaneWidget(self, axis, show):
        self.planes[axis].SetEnabled(show)
    
    def TogglePlaneWidget(self, axis):
        show = not self.planes[axis].GetEnabled()
        self.planes[axis].SetEnabled(show)
    
    def togglePlanesOn(self):
        for i in range(3):
            self.planes[i].On()
    
    def GetCoordinate(self):
        return self.coordinate
        
    def SetCoordinate(self, coor):

        self.coordinate = coor
        for i in range(3):
            self.planes[i].GetRepresentation().SetOrigin(coor[0], coor[1], coor[2])
        self.__UpdateCross()
    
    def __UpdateCross(self):
        p = self.cross.GetPoints()
        x,y,z = self.coordinate[0], self.coordinate[1], self.coordinate[2]
        X,Y,Z = self.dataShape[0], self.dataShape[1], self.dataShape[2] 
        p.SetPoint(0,  0,y,z)
        p.SetPoint(1,  X,y,z)
        p.SetPoint(2,  x,0,z)
        p.SetPoint(3,  x,Y,z)
        p.SetPoint(4,  x,y,0)
        p.SetPoint(5,  x,y,Z)
        self.cross.Modified()
    
    def __PlanePositionCallback(self, obj, event):
        newCoordinate = [int(self.planes[i].GetRepresentation().GetOrigin()[i]) \
                         for i in range(3)]
        axis = -1
        for i in range(3):
            
            if newCoordinate[i] != self.coordinate[i]: axis = i; break
        if axis < 0: return
        if newCoordinate[axis] >= self.dataShape[axis]: newCoordinate[axis] = self.dataShape[axis]-1
                         
        self.__UpdateCross()
        self.lastChangedAxis = axis
        
        self.coordinate = newCoordinate
        #print "__PlanePositionCallback: setting coordinate to", self.coordinate
        self.InvokeEvent("CoordinatesEvent")

import math, logging, time

from wslink import register as exportRpc

import vtk
from vtk.web import protocols as vtk_protocols
from vtkmodules.vtkCommonCore import vtkCommand

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

vtkmath = vtk.vtkMath()

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

def calcAngleBetweenTwoVectors(A, B, C) -> float:
    BA = [A[0] - B[0], A[1] - B[1], A[2] - B[2]]
    BC = [C[0] - B[0], C[1] - B[1], C[2] - B[2]]
    radianAngle = vtkmath.AngleBetweenVectors(BA, BC) # radian unit
    degreeAngle = vtkmath.DegreesFromRadians(radianAngle) # degree unit
    # BA x BC (Cross product)
    crossProduct = [
        BA[1] * BC[2] - BA[2] * BC[1],
        BA[2] * BC[0] - BA[0] * BC[2],
        BA[0] * BC[1] - BA[1] * BC[0]
    ]
    return degreeAngle if crossProduct[2] < 0 else -degreeAngle

class MPRViewer(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self.dicomDirPath = "/home/itadmin/workingspace/dicom_data/KHONGTIEM"
        self.colors = vtk.vtkNamedColors()

        self.initialize()

        self.initCenterlineAxialView()
        self.initCenterlineCoronalView()
        self.initCenterlineSagittalView()

        self.initWidgetsAxialView()
        self.initWidgetsCoronalView()
        self.initWidgetsSagittalView()

        # Used to save current position
        self.currentSphereWidgetCenter = None
        self.currentSphereWidgetCenterRotateLinesAxial = None

    def initialize(self) -> None:
        self.reader = vtk.vtkDICOMImageReader()
        self.axial = vtk.vtkMatrix4x4()
        self.coronal = vtk.vtkMatrix4x4()
        self.sagittal = vtk.vtkMatrix4x4()
        self.rotationMatrix = vtk.vtkMatrix4x4()
        self.resultMatrix = vtk.vtkMatrix4x4()
        self.resliceAxial = vtk.vtkImageReslice()
        self.resliceCoronal = vtk.vtkImageReslice()
        self.resliceSagittal = vtk.vtkImageReslice()
        self.actorAxial = vtk.vtkImageActor()
        self.actorCoronal = vtk.vtkImageActor()
        self.actorSagittal = vtk.vtkImageActor()
        self.cameraAxialView = vtk.vtkCamera()
        self.cameraCoronalView = vtk.vtkCamera()
        self.cameraSagittalView = vtk.vtkCamera()
        self.rendererAxial = vtk.vtkRenderer()
        self.rendererCoronal = vtk.vtkRenderer()
        self.rendererSagittal = vtk.vtkRenderer()

        self.rendererAxial.SetBackground(0.3, 0.1, 0.1)
        self.rendererCoronal.SetBackground(0.1, 0.3, 0.1)
        self.rendererSagittal.SetBackground(0.1, 0.1, 0.3)

        # Initialize rotation matrix (y-axes)
        self.rotationMatrix.DeepCopy(
            (math.cos(math.radians(0)), 0, math.sin(math.radians(0)), 0, 
            0, 1, 0, 0, 
            -math.sin(math.radians(0)), 0, math.cos(math.radians(0)), 0, 
            0, 0, 0, 1)
        )

    def initCenterlineAxialView(self) -> None:
        greenLineAxial = vtk.vtkLineSource()
        greenLineAxial.SetPoint1(0, 500, 0)
        greenLineAxial.SetPoint2(0, -500, 0)
        greenLineAxial.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(greenLineAxial.GetOutput().GetNumberOfCells())
        for c in range(greenLineAxial.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [0, 255, 0])
        greenLineAxial.GetOutput().GetCellData().SetScalars(colorArray)

        blueLineAxial = vtk.vtkLineSource()
        blueLineAxial.SetPoint1(-500, 0, 0)
        blueLineAxial.SetPoint2(500, 0, 0)
        blueLineAxial.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(blueLineAxial.GetOutput().GetNumberOfCells())
        for c in range(blueLineAxial.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [0, 0, 255])
        blueLineAxial.GetOutput().GetCellData().SetScalars(colorArray)

        linesAxial = vtk.vtkAppendPolyData()
        linesAxial.AddInputData(greenLineAxial.GetOutput())
        linesAxial.AddInputData(blueLineAxial.GetOutput())
        linesAxial.Update()

        linesAxialMapper = vtk.vtkPolyDataMapper()
        linesAxialMapper.SetInputConnection(linesAxial.GetOutputPort())

        self.linesAxialActor = vtk.vtkActor()
        self.linesAxialActor.SetMapper(linesAxialMapper)
        self.linesAxialActor.GetProperty().SetLineWidth(1)
        self.linesAxialActor.SetOrigin(0, 0, 0)
        
    def initCenterlineCoronalView(self) -> None:
        greenLineCoronal = vtk.vtkLineSource()
        greenLineCoronal.SetPoint1(0, 0, -500)
        greenLineCoronal.SetPoint2(0, 0, 500)
        greenLineCoronal.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(greenLineCoronal.GetOutput().GetNumberOfCells())
        for c in range(greenLineCoronal.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [0, 255, 0])
        greenLineCoronal.GetOutput().GetCellData().SetScalars(colorArray)

        redLineCoronal = vtk.vtkLineSource()
        redLineCoronal.SetPoint1(-500, 0, 0)
        redLineCoronal.SetPoint2(500, 0, 0)
        redLineCoronal.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(redLineCoronal.GetOutput().GetNumberOfCells())
        for c in range(redLineCoronal.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [255, 0, 0])
        redLineCoronal.GetOutput().GetCellData().SetScalars(colorArray)

        linesCoronal = vtk.vtkAppendPolyData()
        linesCoronal.AddInputData(greenLineCoronal.GetOutput())
        linesCoronal.AddInputData(redLineCoronal.GetOutput())
        linesCoronal.Update()

        linesCoronalMapper = vtk.vtkPolyDataMapper()
        linesCoronalMapper.SetInputConnection(linesCoronal.GetOutputPort())

        self.linesCoronalActor = vtk.vtkActor()
        self.linesCoronalActor.SetMapper(linesCoronalMapper)
        self.linesCoronalActor.GetProperty().SetLineWidth(1)
        self.linesCoronalActor.SetOrigin(0, 0, 0)

    def initCenterlineSagittalView(self) -> None:
        blueLineSagittal = vtk.vtkLineSource()
        blueLineSagittal.SetPoint1(0, 0, -500)
        blueLineSagittal.SetPoint2(0, 0, 500)
        blueLineSagittal.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(blueLineSagittal.GetOutput().GetNumberOfCells())
        for c in range(blueLineSagittal.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [0, 0, 255])
        blueLineSagittal.GetOutput().GetCellData().SetScalars(colorArray)

        redLineSagittal = vtk.vtkLineSource()
        redLineSagittal.SetPoint1(0, -500, 0)
        redLineSagittal.SetPoint2(0, 500, 0)
        redLineSagittal.Update()

        colorArray = vtk.vtkUnsignedCharArray()
        colorArray.SetNumberOfComponents(3)
        colorArray.SetNumberOfTuples(redLineSagittal.GetOutput().GetNumberOfCells())
        for c in range(redLineSagittal.GetOutput().GetNumberOfCells()):
            colorArray.SetTuple(c, [255, 0, 0])
        redLineSagittal.GetOutput().GetCellData().SetScalars(colorArray)

        linesSagittal = vtk.vtkAppendPolyData()
        linesSagittal.AddInputData(blueLineSagittal.GetOutput())
        linesSagittal.AddInputData(redLineSagittal.GetOutput())
        linesSagittal.Update()

        linesSagittalMapper = vtk.vtkPolyDataMapper()
        linesSagittalMapper.SetInputConnection(linesSagittal.GetOutputPort())

        self.linesSagittalActor = vtk.vtkActor()
        self.linesSagittalActor.SetMapper(linesSagittalMapper)
        self.linesSagittalActor.GetProperty().SetLineWidth(1)
        self.linesSagittalActor.SetOrigin(0, 0, 0)

    def initWidgetsAxialView(self) -> None:
        self.sphereWidgetAxial = vtk.vtkSphereWidget()
        self.sphereWidgetAxial.SetRadius(8)
        self.sphereWidgetAxial.SetRepresentationToSurface()
        self.sphereWidgetAxial.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetAxial.GetSelectedSphereProperty().SetOpacity(0)
        self.sphereWidgetAxial.SetCurrentRenderer(self.rendererAxial)

        self.sphereWidgetInteractionRotateGreenLineAxial = vtk.vtkSphereWidget()
        self.sphereWidgetInteractionRotateGreenLineAxial.SetRadius(6)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetRepresentationToSurface()
        self.sphereWidgetInteractionRotateGreenLineAxial.GetSphereProperty().SetColor(self.colors.GetColor3d("green"))
        self.sphereWidgetInteractionRotateGreenLineAxial.GetSelectedSphereProperty().SetOpacity(0)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetCurrentRenderer(self.rendererAxial)

    def initWidgetsCoronalView(self) -> None:
        self.sphereWidgetCoronal = vtk.vtkSphereWidget()
        self.sphereWidgetCoronal.SetRadius(8)
        self.sphereWidgetCoronal.SetRepresentationToSurface()
        self.sphereWidgetCoronal.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetCoronal.GetSelectedSphereProperty().SetOpacity(0)
        self.sphereWidgetCoronal.SetCurrentRenderer(self.rendererCoronal)

    def initWidgetsSagittalView(self) -> None:
        self.sphereWidgetSagittal = vtk.vtkSphereWidget()
        self.sphereWidgetSagittal.SetRadius(8)
        self.sphereWidgetSagittal.SetRepresentationToSurface()
        self.sphereWidgetSagittal.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetSagittal.GetSelectedSphereProperty().SetOpacity(0)
        self.sphereWidgetSagittal.SetCurrentRenderer(self.rendererSagittal)

    def turnOnWidgets(self) -> None:
        self.sphereWidgetAxial.On()
        self.sphereWidgetInteractionRotateGreenLineAxial.On()
        # self.sphereWidgetCoronal.On()
        # self.sphereWidgetSagittal.On()

    def turnOffWidgets(self) -> None:
        self.sphereWidgetAxial.Off()
        self.sphereWidgetInteractionRotateGreenLineAxial.Off()
        self.sphereWidgetCoronal.Off()
        self.sphereWidgetSagittal.Off()

    @exportRpc("vtk.initialize")
    def createVisualization(self) -> None:
        renderWindowAxial = self.getApplication().GetObjectIdMap().GetActiveObject("AXIAL_VIEW")
        renderWindowInteractorAxial = renderWindowAxial.GetInteractor()
        renderWindowCoronal = self.getApplication().GetObjectIdMap().GetActiveObject("CORONAL_VIEW")
        renderWindowInteractorCoronal = renderWindowCoronal.GetInteractor()
        renderWindowSagittal = self.getApplication().GetObjectIdMap().GetActiveObject("SAGITTAL_VIEW")
        renderWindowInteractorSagittal = renderWindowSagittal.GetInteractor()
        
        # Reader
        self.reader.SetDirectoryName(self.dicomDirPath)
        self.reader.Update()
        imageData = self.reader.GetOutput()
        center = imageData.GetCenter()
        (xMin, xMax, yMin, yMax, zMin, zMax) = imageData.GetBounds()

        # Setup widgets in axial view
        self.sphereWidgetAxial.SetCenter(center)
        self.sphereWidgetAxial.SetInteractor(renderWindowInteractorAxial)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetInteractor(renderWindowInteractorAxial)

        # Setup widgets in coronal view
        self.sphereWidgetCoronal.SetCenter(center)
        self.sphereWidgetCoronal.SetInteractor(renderWindowInteractorCoronal)

        # Setup widgets in sagittal view
        self.sphereWidgetSagittal.SetCenter(center)
        self.sphereWidgetSagittal.SetInteractor(renderWindowInteractorSagittal)

        # Matrices for axial, coronal, and sagittal view orientations
        # Model matrix = Translation matrix
        self.axial.DeepCopy(
            (1, 0, 0, center[0], 
             0, 1, 0, center[1], 
             0, 0, 1, center[2], 
             0, 0, 0, 1)
        )
        # Model matrix = Translation matrix . Rotation matrix(X)
        self.coronal.DeepCopy(
            (1, 0, 0, center[0], 
             0, 0, 1, center[1], 
             0,-1, 0, center[2], 
             0, 0, 0, 1)
        )
        # Model matrix = Translation matrix . Rotation matrix(X) . Rotation matrix(Y)
        self.sagittal.DeepCopy(
            (0, 0,-1, center[0], 
             1, 0, 0, center[1], 
             0,-1, 0, center[2], 
             0, 0, 0, 1)
        )

        # Extract a slice in the desired orientation
        self.resliceAxial.SetInputData(imageData)
        self.resliceAxial.SetOutputDimensionality(2)
        self.resliceAxial.SetResliceAxes(self.axial)
        self.resliceAxial.SetInterpolationModeToLinear()

        self.resliceCoronal.SetInputData(imageData)
        self.resliceCoronal.SetOutputDimensionality(2)
        self.resliceCoronal.SetResliceAxes(self.coronal)
        self.resliceCoronal.SetInterpolationModeToLinear()
        
        self.resliceSagittal.SetInputData(imageData)
        self.resliceSagittal.SetOutputDimensionality(2)
        self.resliceSagittal.SetResliceAxes(self.sagittal)
        self.resliceSagittal.SetInterpolationModeToLinear()

        # Display dicom
        self.actorAxial.GetMapper().SetInputConnection(self.resliceAxial.GetOutputPort())
        self.actorCoronal.GetMapper().SetInputConnection(self.resliceCoronal.GetOutputPort())
        self.actorSagittal.GetMapper().SetInputConnection(self.resliceSagittal.GetOutputPort())

        # Set position and direction of dicom
        self.actorAxial.SetUserMatrix(self.axial)
        self.actorCoronal.SetUserMatrix(self.coronal)
        self.actorSagittal.SetUserMatrix(self.sagittal)

        # Renderers
        # self.rendererAxial.AddActor(self.actorAxial)
        self.rendererAxial.AddActor(self.linesAxialActor)
        self.cameraAxialView.SetPosition(center[0], center[1], 3.5*zMax)
        self.cameraAxialView.SetFocalPoint(center)
        self.cameraAxialView.SetViewUp(0, 1, 0)
        self.cameraAxialView.SetThickness(3.5*zMax)
        self.rendererAxial.SetActiveCamera(self.cameraAxialView)

        # self.rendererCoronal.AddActor(self.actorCoronal)
        # self.rendererCoronal.AddActor(self.linesCoronalActor)
        # self.cameraCoronalView.SetPosition(center[0], 3.5*yMax, center[2])
        # self.cameraCoronalView.SetFocalPoint(center)
        # self.cameraCoronalView.SetViewUp(0, 0, -1)
        # self.cameraCoronalView.SetThickness(3.5*yMax)
        # self.rendererCoronal.SetActiveCamera(self.cameraCoronalView)

        # self.rendererSagittal.AddActor(self.actorSagittal)
        # self.rendererSagittal.AddActor(self.linesSagittalActor)
        # self.cameraSagittalView.SetPosition(3.5*xMax, center[1], center[2])
        # self.cameraSagittalView.SetFocalPoint(center)
        # self.cameraSagittalView.SetViewUp(0, 0, -1)
        # self.cameraSagittalView.SetThickness(3.5*xMax)
        # self.rendererSagittal.SetActiveCamera(self.cameraSagittalView)

        # Add renderer object into render window object
        renderWindowAxial.AddRenderer(self.rendererAxial)
        # renderWindowCoronal.AddRenderer(self.rendererCoronal)
        # renderWindowSagittal.AddRenderer(self.rendererSagittal)

        # Set lines in axial view
        self.linesAxialActor.SetPosition(center)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter(center[0], (yMax + center[1])/2, center[2])

        # Set lines in coronal view
        # self.linesCoronalActor.SetPosition(center)

        # Set lines in sagittal view
        # self.linesSagittalActor.SetPosition(center)

        # Create callback function for sphere widget interaction
        self.currentSphereWidgetCenter = {
            "axial": self.sphereWidgetAxial.GetCenter(),
            "coronal": self.sphereWidgetCoronal.GetCenter(),
            "sagittal": self.sphereWidgetSagittal.GetCenter()
        }
        self.currentSphereWidgetCenterRotateLinesAxial = {
            "green": self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()
        }

        def interactionEventHandleTranslateLines_AxialView(obj, event) -> None:
            newPosition = obj.GetCenter()
            translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]

            # Translate lines in axial view
            self.linesAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            # self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            # self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            # self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in sagittal view
            # self.sphereWidgetSagittal.SetCenter(newPosition)
            # Translate lines in sagital view
            # self.linesSagittalActor.SetPosition(newPosition)

            # self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            # self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            # self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in coronal view
            # self.sphereWidgetCoronal.SetCenter(newPosition)
            # Translate lines in coronal view
            # self.linesCoronalActor.SetPosition(newPosition)

            self.currentSphereWidgetCenter["axial"] = newPosition
            self.currentSphereWidgetCenter["sagittal"] = newPosition
            self.currentSphereWidgetCenter["coronal"] = newPosition
            
            renderWindowAxial.Render()
            # renderWindowCoronal.Render()
            # renderWindowSagittal.Render()

        def interactionEventHandleTranslateLines_CoronalView(obj, event) -> None:
            newPosition = obj.GetCenter()
            translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["coronal"][i] for i in range(3)]

            # Translate lines in coronal view
            self.linesCoronalActor.SetPosition(newPosition)

            self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in axial view
            self.sphereWidgetAxial.SetCenter(newPosition)
            # Translate lines in axial view
            self.linesAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in sagittal view
            self.sphereWidgetSagittal.SetCenter(newPosition)
            # Translate lines in sagittal view
            self.linesSagittalActor.SetPosition(newPosition)

            self.currentSphereWidgetCenter["axial"] = newPosition
            self.currentSphereWidgetCenter["sagittal"] = newPosition
            self.currentSphereWidgetCenter["coronal"] = newPosition

            renderWindowAxial.Render()
            renderWindowCoronal.Render()
            renderWindowSagittal.Render()

        def interactionEventHandleTranslateLines_SagittalView(obj, event) -> None:
            newPosition = obj.GetCenter()
            translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["sagittal"][i] for i in range(3)]

            # Translate lines in sagittal view
            self.linesSagittalActor.SetPosition(newPosition)

            self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in axial view
            self.sphereWidgetAxial.SetCenter(newPosition)
            # Translate lines in axial view
            self.linesAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in coronal view
            self.sphereWidgetCoronal.SetCenter(newPosition)
            # Translate lines in coronal view
            self.linesCoronalActor.SetPosition(newPosition)

            self.currentSphereWidgetCenter["axial"] = newPosition
            self.currentSphereWidgetCenter["sagittal"] = newPosition
            self.currentSphereWidgetCenter["coronal"] = newPosition

            renderWindowAxial.Render()
            renderWindowCoronal.Render()
            renderWindowSagittal.Render()

        def interactionEventHandleRotateGreenLine_AxialView(obj, event) -> None:
            start = time.time()
            newPosition = obj.GetCenter()
            # Calculate rotation angle (degree unit)
            angle = calcAngleBetweenTwoVectors(self.currentSphereWidgetCenterRotateLinesAxial["green"], self.currentSphereWidgetCenter["axial"], newPosition)

            # Rotate lines in axial view
            self.linesAxialActor.RotateZ(-angle)

            # Create rotate matrix (y-axes)
            # self.rotationMatrix.SetElement(0, 0, math.cos(math.radians(angle)))
            # self.rotationMatrix.SetElement(0, 2, math.sin(math.radians(angle)))
            # self.rotationMatrix.SetElement(2, 0, -math.sin(math.radians(angle)))
            # self.rotationMatrix.SetElement(2, 2, math.cos(math.radians(angle)))
            
            # Set transform matrix (sagittal view)
            # vtk.vtkMatrix4x4.Multiply4x4(self.resliceSagittal.GetResliceAxes(), self.rotationMatrix, self.resultMatrix)
            # for i in range(4):
            #     for j in range(4):
            #         self.resliceSagittal.GetResliceAxes().SetElement(i, j, self.resultMatrix.GetElement(i, j))
            # self.linesSagittalActor.RotateZ(-angle)
            # self.rendererSagittal.GetActiveCamera().Azimuth(angle)

            # Set transform matrix (coronal view)
            # vtk.vtkMatrix4x4.Multiply4x4(self.resliceCoronal.GetResliceAxes(), self.rotationMatrix, self.resultMatrix)
            # for i in range(4):
            #     for j in range(4):
            #         self.resliceCoronal.GetResliceAxes().SetElement(i, j, self.resultMatrix.GetElement(i, j))
            # self.linesCoronalActor.RotateZ(-angle)
            # self.rendererCoronal.GetActiveCamera().Azimuth(angle)

            self.currentSphereWidgetCenterRotateLinesAxial["green"] = newPosition

            renderWindowAxial.Render()
            # renderWindowCoronal.Render()
            # renderWindowSagittal.Render()
            stop = time.time()
            # logging.info(f"total rotation time: {stop - start}, rotation angle: {angle}")
        
        self.sphereWidgetAxial.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_AxialView)
        self.sphereWidgetInteractionRotateGreenLineAxial.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleRotateGreenLine_AxialView)
        # self.sphereWidgetCoronal.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_CoronalView)
        # self.sphereWidgetSagittal.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_SagittalView)

        # Turn on sphere widget
        self.turnOnWidgets()

        renderWindowAxial.Render()
        # renderWindowCoronal.Render()
        # renderWindowSagittal.Render()

        self.getApplication().InvalidateCache(renderWindowAxial)
        # self.getApplication().InvalidateCache(renderWindowCoronal)
        # self.getApplication().InvalidateCache(renderWindowSagittal)
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("viewport.mouse.zoom.wheel")
    def updateZoomFromWheel(self, event):
        if 'Start' in event["type"]:
            self.getApplication().InvokeEvent(vtkCommand.StartInteractionEvent)

        # MouseWheelForwardEvent: event["spinY"] < 0
        # MouseWheelBackwardEvent: event["spinY"] > 0
        viewId = int(event.get("view"))
        # Axial view
        if viewId == 1:
            sliceSpacing = self.resliceAxial.GetOutput().GetSpacing()[2]
            cameraPosition = self.rendererAxial.GetActiveCamera().GetPosition()
            focalPoint = self.rendererAxial.GetActiveCamera().GetFocalPoint()
            if "spinY" in event and event.get("spinY") and event.get("spinY") < 0:
                # move the center point that we are slicing through
                projectionVector = [focalPoint[i] - cameraPosition[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(projectionVector)
                temp = [(sliceSpacing/norm) * projectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["axial"][i] + temp[i] for i in range(3)]
                self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)
            elif "spinY" in event and event.get("spinY") and event.get("spinY") > 0:
                # move the center point that we are slicing through
                invertProjectionVector = [cameraPosition[i] - focalPoint[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(invertProjectionVector)
                temp = [(sliceSpacing/norm) * invertProjectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["axial"][i] + temp[i] for i in range(3)]
                self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)
        # Coronal view
        elif viewId == 2:
            sliceSpacing = self.resliceCoronal.GetOutput().GetSpacing()[2]
            cameraPosition = self.rendererCoronal.GetActiveCamera().GetPosition()
            focalPoint = self.rendererCoronal.GetActiveCamera().GetFocalPoint()
            if "spinY" in event and event["spinY"] and event["spinY"] < 0:
                # move the center point that we are slicing through
                projectionVector = [focalPoint[i] - cameraPosition[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(projectionVector)
                temp = [(sliceSpacing/norm) * projectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["coronal"][i] + temp[i] for i in range(3)]
                self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)
                
                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)
            elif "spinY" in event and event["spinY"] and event["spinY"] > 0:
                # move the center point that we are slicing through
                invertProjectionVector = [cameraPosition[i] - focalPoint[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(invertProjectionVector)
                temp = [(sliceSpacing/norm) * invertProjectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["coronal"][i] + temp[i] for i in range(3)]
                self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)
                
                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)
        # Sagittal view
        elif viewId == 3:
            sliceSpacing = self.resliceSagittal.GetOutput().GetSpacing()[2]
            cameraPosition = self.rendererSagittal.GetActiveCamera().GetPosition()
            focalPoint = self.rendererSagittal.GetActiveCamera().GetFocalPoint()
            if "spinY" in event and event["spinY"] and event["spinY"] < 0:
                # move the center point that we are slicing through
                projectionVector = [focalPoint[i] - cameraPosition[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(projectionVector)
                temp = [(sliceSpacing/norm) * projectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["sagittal"][i] + temp[i] for i in range(3)]
                self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)
            elif "spinY" in event and event["spinY"] and event["spinY"] > 0:
                # move the center point that we are slicing through
                invertProjectionVector = [cameraPosition[i] - focalPoint[i] for i in range(3)]
                norm = vtk.vtkMath.Norm(invertProjectionVector)
                temp = [(sliceSpacing/norm) * invertProjectionVector[i] for i in range(3)]
                newPosition = [self.currentSphereWidgetCenter["sagittal"][i] + temp[i] for i in range(3)]
                self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
                self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
                self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.linesSagittalActor.SetPosition(newPosition)

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.linesAxialActor.SetPosition(newPosition)
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.currentSphereWidgetCenterRotateLinesAxial["green"][i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.linesCoronalActor.SetPosition(newPosition)

        self.currentSphereWidgetCenter["axial"] = self.sphereWidgetAxial.GetCenter()
        self.currentSphereWidgetCenter["coronal"] = self.sphereWidgetCoronal.GetCenter()
        self.currentSphereWidgetCenter["sagittal"] = self.sphereWidgetSagittal.GetCenter()

        self.getApplication().GetObjectIdMap().GetActiveObject("AXIAL_VIEW").Render()
        self.getApplication().GetObjectIdMap().GetActiveObject("CORONAL_VIEW").Render()
        self.getApplication().GetObjectIdMap().GetActiveObject("SAGITTAL_VIEW").Render()

        if 'End' in event["type"]:
            self.getApplication().InvokeEvent(vtkCommand.EndInteractionEvent)

    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindow.GetRenderers().GetFirstRenderer().ResetCamera()
        renderWindow.Render()
        self.getApplication().InvalidateCache(renderWindow)
        self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.cone.resolution.update")
    def updateResolution(self, resolution):
        self.cone.SetResolution(resolution)
        renderWindow = self.getView('-1')
        # renderWindow.Modified() # either modified or render
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

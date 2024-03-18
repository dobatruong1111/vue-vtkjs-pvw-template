import math, logging

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

class VtkCone(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self.dicomDirPath = "D:/workingspace/Python/dicom-data/17025648 HOANG VAN KHIEN/24.0203.003678 Chup CLVT he dong mach canh co tiem thuoc can quang tu 64128 d/CT 0.625mm KHONG THUOC"
        # Color vtk-class
        self.colors = vtk.vtkNamedColors()

        # Pipeline main
        self.reader = vtk.vtkDICOMImageReader()
        self.axial = vtk.vtkMatrix4x4()
        self.coronal = vtk.vtkMatrix4x4()
        self.sagittal = vtk.vtkMatrix4x4()
        self.transformMatrix = vtk.vtkMatrix4x4()
        self.resultMatrix = vtk.vtkMatrix4x4()
        self.resliceAxial = vtk.vtkImageReslice()
        self.resliceCoronal = vtk.vtkImageReslice()
        self.resliceSagittal = vtk.vtkImageReslice()
        self.actorAxial = vtk.vtkImageActor()
        self.actorCoronal = vtk.vtkImageActor()
        self.actorSagittal = vtk.vtkImageActor()
        self.rendererAxial = vtk.vtkRenderer()
        self.rendererCoronal = vtk.vtkRenderer()
        self.rendererSagittal = vtk.vtkRenderer()

        # Init widgets in axial view
        self.sphereWidgetAxial = vtk.vtkSphereWidget()
        self.sphereWidgetInteractionRotateGreenLineAxial = vtk.vtkSphereWidget()
        self.greenLineAxial = vtk.vtkLineSource()
        self.greenLineAxialMapper = vtk.vtkPolyDataMapper()
        self.greenLineAxialActor = vtk.vtkActor()
        self.blueLineAxial = vtk.vtkLineSource()
        self.blueLineAxialMapper = vtk.vtkPolyDataMapper()
        self.blueLineAxialActor = vtk.vtkActor()

        # Init widgets in coronal view
        self.sphereWidgetCoronal = vtk.vtkSphereWidget()
        self.greenLineCoronal = vtk.vtkLineSource()
        self.greenLineCoronalMapper = vtk.vtkPolyDataMapper()
        self.greenLineCoronalActor = vtk.vtkActor()
        self.redLineCoronal = vtk.vtkLineSource()
        self.redLineCoronalMapper = vtk.vtkPolyDataMapper()
        self.redLineCoronalActor = vtk.vtkActor()

        # Init widgets in sagittal view
        self.sphereWidgetSagittal = vtk.vtkSphereWidget()
        self.blueLineSagittal = vtk.vtkLineSource()
        self.blueLineSagittalMapper = vtk.vtkPolyDataMapper()
        self.blueLineSagittalActor = vtk.vtkActor()
        self.redLineSagittal = vtk.vtkLineSource()
        self.redLineSagittalMapper = vtk.vtkPolyDataMapper()
        self.redLineSagittalActor = vtk.vtkActor()

        # Used to save current position
        self.currentSphereWidgetCenter = None
        self.currentSphereWidgetCenterRotateLinesAxial = None

        # Init cameras
        self.cameraAxialView = vtk.vtkCamera()
        self.cameraCoronalView = vtk.vtkCamera()
        self.cameraSagittalView = vtk.vtkCamera()

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        renderWindowAxial = self.getApplication().GetObjectIdMap().GetActiveObject("AXIAL_VIEW")
        renderWindowInteractorAxial = renderWindowAxial.GetInteractor()
        renderWindowCoronal = self.getApplication().GetObjectIdMap().GetActiveObject("CORONAL_VIEW")
        renderWindowInteractorCoronal = renderWindowCoronal.GetInteractor()
        renderWindowSagittal = self.getApplication().GetObjectIdMap().GetActiveObject("SAGITTAL_VIEW")
        renderWindowInteractorSagittal = renderWindowSagittal.GetInteractor()

        # Setup widgets in axial view
        self.greenLineAxialMapper.SetInputConnection(self.greenLineAxial.GetOutputPort())
        self.greenLineAxialActor.SetMapper(self.greenLineAxialMapper)
        self.greenLineAxialActor.GetProperty().SetColor(self.colors.GetColor3d("Green"))
        self.blueLineAxialMapper.SetInputConnection(self.blueLineAxial.GetOutputPort())
        self.blueLineAxialActor.SetMapper(self.blueLineAxialMapper)
        self.blueLineAxialActor.GetProperty().SetColor(self.colors.GetColor3d("Blue"))

        # Setup widgets in coronal view
        self.greenLineCoronalMapper.SetInputConnection(self.greenLineCoronal.GetOutputPort())
        self.greenLineCoronalActor.SetMapper(self.greenLineCoronalMapper)
        self.greenLineCoronalActor.GetProperty().SetColor(self.colors.GetColor3d("Green"))
        self.redLineCoronalMapper.SetInputConnection(self.redLineCoronal.GetOutputPort())
        self.redLineCoronalActor.SetMapper(self.redLineCoronalMapper)
        self.redLineCoronalActor.GetProperty().SetColor(self.colors.GetColor3d("Red"))

        # Setup widgets in sagittal view
        self.blueLineSagittalMapper.SetInputConnection(self.blueLineSagittal.GetOutputPort())
        self.blueLineSagittalActor.SetMapper(self.blueLineSagittalMapper)
        self.blueLineSagittalActor.GetProperty().SetColor(self.colors.GetColor3d("Blue"))
        self.redLineSagittalMapper.SetInputConnection(self.redLineSagittal.GetOutputPort())
        self.redLineSagittalActor.SetMapper(self.redLineSagittalMapper)
        self.redLineSagittalActor.GetProperty().SetColor(self.colors.GetColor3d("Red"))

        # Reader
        self.reader.SetDirectoryName(self.dicomDirPath)
        self.reader.Update()
        imageData = self.reader.GetOutput()
        center = imageData.GetCenter()
        (xMin, xMax, yMin, yMax, zMin, zMax) = imageData.GetBounds()

        # Setup widgets in axial view
        self.sphereWidgetAxial.SetCenter(center)
        self.sphereWidgetAxial.SetRadius(8)
        self.sphereWidgetAxial.SetInteractor(renderWindowInteractorAxial)
        self.sphereWidgetAxial.SetRepresentationToSurface()
        self.sphereWidgetAxial.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetAxial.GetSelectedSphereProperty().SetOpacity(0)
        # Markup a position to rotate a green line in axial view
        self.sphereWidgetInteractionRotateGreenLineAxial.SetRadius(6)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetInteractor(renderWindowInteractorAxial)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetRepresentationToSurface()
        self.sphereWidgetInteractionRotateGreenLineAxial.GetSphereProperty().SetColor(self.colors.GetColor3d("green"))
        self.sphereWidgetInteractionRotateGreenLineAxial.GetSelectedSphereProperty().SetOpacity(0)

        # Setup widgets in coronal view
        self.sphereWidgetCoronal.SetCenter(center)
        self.sphereWidgetCoronal.SetRadius(8)
        self.sphereWidgetCoronal.SetInteractor(renderWindowInteractorCoronal)
        self.sphereWidgetCoronal.SetRepresentationToSurface()
        self.sphereWidgetCoronal.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetCoronal.GetSelectedSphereProperty().SetOpacity(0)

        # Setup widgets in sagittal view
        self.sphereWidgetSagittal.SetCenter(center)
        self.sphereWidgetSagittal.SetRadius(8)
        self.sphereWidgetSagittal.SetInteractor(renderWindowInteractorSagittal)
        self.sphereWidgetSagittal.SetRepresentationToSurface()
        self.sphereWidgetSagittal.GetSphereProperty().SetColor(self.colors.GetColor3d("Tomato"))
        self.sphereWidgetSagittal.GetSelectedSphereProperty().SetOpacity(0)

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
        self.rendererAxial.AddActor(self.actorAxial)
        self.rendererAxial.AddActor(self.greenLineAxialActor)
        self.rendererAxial.AddActor(self.blueLineAxialActor)
        # self.rendererAxial.SetViewport(0, 0, 0.5, 1)
        self.rendererAxial.SetBackground(0.3, 0.1, 0.1)
        self.cameraAxialView.SetPosition(center[0], center[1], 3.5*zMax)
        self.cameraAxialView.SetFocalPoint(center)
        self.cameraAxialView.SetViewUp(0, 1, 0)
        self.cameraAxialView.SetThickness(3.5*zMax)
        self.rendererAxial.SetActiveCamera(self.cameraAxialView)
        self.sphereWidgetAxial.SetCurrentRenderer(self.rendererAxial)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetCurrentRenderer(self.rendererAxial)

        self.rendererCoronal.AddActor(self.actorCoronal)
        self.rendererCoronal.AddActor(self.greenLineCoronalActor)
        self.rendererCoronal.AddActor(self.redLineCoronalActor)
        # self.rendererCoronal.SetViewport(0.5, 0, 1, 0.5)
        self.rendererCoronal.SetBackground(0.1, 0.3, 0.1)
        self.cameraCoronalView.SetPosition(center[0], 3.5*yMax, center[2])
        self.cameraCoronalView.SetFocalPoint(center)
        self.cameraCoronalView.SetViewUp(0, 0, -1)
        self.cameraCoronalView.SetThickness(3.5*yMax)
        self.rendererCoronal.SetActiveCamera(self.cameraCoronalView)
        self.sphereWidgetCoronal.SetCurrentRenderer(self.rendererCoronal)

        self.rendererSagittal.AddActor(self.actorSagittal)
        self.rendererSagittal.AddActor(self.blueLineSagittalActor)
        self.rendererSagittal.AddActor(self.redLineSagittalActor)
        # self.rendererSagittal.SetViewport(0.5, 0.5, 1, 1)
        self.rendererSagittal.SetBackground(0.1, 0.1, 0.3)
        self.cameraSagittalView.SetPosition(3.5*xMax, center[1], center[2])
        self.cameraSagittalView.SetFocalPoint(center)
        self.cameraSagittalView.SetViewUp(0, 0, -1)
        self.cameraSagittalView.SetThickness(3.5*xMax)
        self.rendererSagittal.SetActiveCamera(self.cameraSagittalView)
        self.sphereWidgetSagittal.SetCurrentRenderer(self.rendererSagittal)

        # Add renderer object into render window object
        renderWindowAxial.AddRenderer(self.rendererAxial)
        renderWindowCoronal.AddRenderer(self.rendererCoronal)
        renderWindowSagittal.AddRenderer(self.rendererSagittal)

        # Set lines in axial view
        self.greenLineAxial.SetPoint1(0, yMax, 0)
        self.greenLineAxial.SetPoint2(0, -yMax, 0)
        self.greenLineAxialActor.SetOrigin(0, 0, 0)
        self.greenLineAxialActor.SetPosition(center)
        self.blueLineAxial.SetPoint1(-xMax, 0, 0)
        self.blueLineAxial.SetPoint2(xMax, 0, 0)
        self.blueLineAxialActor.SetOrigin(0, 0, 0)
        self.blueLineAxialActor.SetPosition(center)
        self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter(center[0], (yMax + center[1])/2, center[2])

        # Set lines in coronal view
        self.greenLineCoronal.SetPoint1(0, 0, -zMax)
        self.greenLineCoronal.SetPoint2(0, 0, zMax)
        self.greenLineCoronalActor.SetOrigin(0, 0, 0)
        self.greenLineCoronalActor.SetPosition(center)
        self.redLineCoronal.SetPoint1(-xMax, 0, 0)
        self.redLineCoronal.SetPoint2(xMax, 0, 0)
        self.redLineCoronalActor.SetOrigin(0, 0, 0)
        self.redLineCoronalActor.SetPosition(center)

        # Set lines in sagittal view
        self.blueLineSagittal.SetPoint1(0, 0, -zMax)
        self.blueLineSagittal.SetPoint2(0, 0, zMax)
        self.blueLineSagittalActor.SetOrigin(0, 0, 0)
        self.blueLineSagittalActor.SetPosition(center)
        self.redLineSagittal.SetPoint1(0, -yMax, 0)
        self.redLineSagittal.SetPoint2(0, yMax, 0)
        self.redLineSagittalActor.SetOrigin(0, 0, 0)
        self.redLineSagittalActor.SetPosition(center)

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
            self.greenLineAxialActor.SetPosition(newPosition)
            self.blueLineAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in sagittal view
            self.sphereWidgetSagittal.SetCenter(newPosition)
            # Translate lines in sagital view
            self.blueLineSagittalActor.SetPosition(newPosition)
            self.redLineSagittalActor.SetPosition(newPosition)

            self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in coronal view
            self.sphereWidgetCoronal.SetCenter(newPosition)
            # Translate lines in coronal view
            self.greenLineCoronalActor.SetPosition(newPosition)
            self.redLineCoronalActor.SetPosition(newPosition)

            self.currentSphereWidgetCenter["axial"] = newPosition
            self.currentSphereWidgetCenter["sagittal"] = newPosition
            self.currentSphereWidgetCenter["coronal"] = newPosition
            renderWindowAxial.Render()
            renderWindowCoronal.Render()
            renderWindowSagittal.Render()

        def interactionEventHandleTranslateLines_CoronalView(obj, event) -> None:
            newPosition = obj.GetCenter()
            translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["coronal"][i] for i in range(3)]

            # Translate lines in coronal view
            self.greenLineCoronalActor.SetPosition(newPosition)
            self.redLineCoronalActor.SetPosition(newPosition)

            self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in axial view
            self.sphereWidgetAxial.SetCenter(newPosition)
            # Translate lines in axial view
            self.greenLineAxialActor.SetPosition(newPosition)
            self.blueLineAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            self.resliceSagittal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceSagittal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceSagittal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in sagittal view
            self.sphereWidgetSagittal.SetCenter(newPosition)
            # Translate lines in sagittal view
            self.blueLineSagittalActor.SetPosition(newPosition)
            self.redLineSagittalActor.SetPosition(newPosition)

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
            self.blueLineSagittalActor.SetPosition(newPosition)
            self.redLineSagittalActor.SetPosition(newPosition)

            self.resliceAxial.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceAxial.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceAxial.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in axial view
            self.sphereWidgetAxial.SetCenter(newPosition)
            # Translate lines in axial view
            self.greenLineAxialActor.SetPosition(newPosition)
            self.blueLineAxialActor.SetPosition(newPosition)
            # Translate a rotation point on green line in axial view
            self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
            self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

            self.resliceCoronal.GetResliceAxes().SetElement(0, 3, newPosition[0])
            self.resliceCoronal.GetResliceAxes().SetElement(1, 3, newPosition[1])
            self.resliceCoronal.GetResliceAxes().SetElement(2, 3, newPosition[2])
            # Translate sphere widget in coronal view
            self.sphereWidgetCoronal.SetCenter(newPosition)
            # Translate lines in coronal view
            self.greenLineCoronalActor.SetPosition(newPosition)
            self.redLineCoronalActor.SetPosition(newPosition)

            self.currentSphereWidgetCenter["axial"] = newPosition
            self.currentSphereWidgetCenter["sagittal"] = newPosition
            self.currentSphereWidgetCenter["coronal"] = newPosition
            renderWindowAxial.Render()
            renderWindowCoronal.Render()
            renderWindowSagittal.Render()

        def interactionEventHandleRotateGreenLine_AxialView(obj, event) -> None:
            newPosition = obj.GetCenter()
            # Calculate rotation angle (degree unit)
            angle = calcAngleBetweenTwoVectors(self.currentSphereWidgetCenterRotateLinesAxial["green"], self.currentSphereWidgetCenter["axial"], newPosition)

            # Rotate lines in axial view
            self.greenLineAxialActor.RotateZ(-angle)
            self.blueLineAxialActor.RotateZ(-angle)

            # Create rotate matrix (y-axes)
            self.transformMatrix.DeepCopy(
                (math.cos(math.radians(angle)), 0, math.sin(math.radians(angle)), 0, 
                0, 1, 0, 0, 
                -math.sin(math.radians(angle)), 0, math.cos(math.radians(angle)), 0, 
                0, 0, 0, 1)
            )
            
            # Set transform matrix (sagittal view)
            vtk.vtkMatrix4x4.Multiply4x4(self.resliceSagittal.GetResliceAxes(), self.transformMatrix, self.resultMatrix)
            for i in range(4):
                for j in range(4):
                    self.resliceSagittal.GetResliceAxes().SetElement(i, j, self.resultMatrix.GetElement(i, j))
            self.redLineSagittalActor.RotateZ(-angle)
            self.rendererSagittal.GetActiveCamera().Azimuth(angle)

            # Set transform matrix (coronal view)
            vtk.vtkMatrix4x4.Multiply4x4(self.resliceCoronal.GetResliceAxes(), self.transformMatrix, self.resultMatrix)
            for i in range(4):
                for j in range(4):
                    self.resliceCoronal.GetResliceAxes().SetElement(i, j, self.resultMatrix.GetElement(i, j))
            self.redLineCoronalActor.RotateZ(-angle)
            self.rendererCoronal.GetActiveCamera().Azimuth(angle)

            self.currentSphereWidgetCenterRotateLinesAxial["green"] = newPosition
            renderWindowAxial.Render()
            renderWindowCoronal.Render()
            renderWindowSagittal.Render()
        
        self.sphereWidgetAxial.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_AxialView)
        self.sphereWidgetInteractionRotateGreenLineAxial.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleRotateGreenLine_AxialView)
        self.sphereWidgetCoronal.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_CoronalView)
        self.sphereWidgetSagittal.AddObserver(vtkCommand.InteractionEvent, interactionEventHandleTranslateLines_SagittalView)

        # Turn on sphere widget
        self.sphereWidgetAxial.On()
        self.sphereWidgetInteractionRotateGreenLineAxial.On()
        self.sphereWidgetCoronal.On()
        self.sphereWidgetSagittal.On()

        renderWindowAxial.Render()
        renderWindowCoronal.Render()
        renderWindowSagittal.Render()

        self.getApplication().InvalidateCache(renderWindowAxial)
        self.getApplication().InvalidateCache(renderWindowCoronal)
        self.getApplication().InvalidateCache(renderWindowSagittal)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    # @exportRpc("vtk.initialize")
    # def createVisualization(self):
    #     renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
    #     renderer = renderWindow.GetRenderers().GetFirstRenderer()

    #     cone = self.cone
    #     mapper = vtk.vtkPolyDataMapper()
    #     actor = vtk.vtkActor()

    #     mapper.SetInputConnection(cone.GetOutputPort())
    #     actor.SetMapper(mapper)

    #     renderer.AddActor(actor)
    #     renderer.ResetCamera()
    #     renderWindow.Render()

    #     sphereRenderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("SPHERE_VIEW")
    #     sphereRenderer = sphereRenderWindow.GetRenderers().GetFirstRenderer()

    #     sphere = self.sphere
    #     sphereMapper = vtk.vtkPolyDataMapper()
    #     sphereActor = vtk.vtkActor()
        
    #     sphereMapper.SetInputConnection(sphere.GetOutputPort())
    #     sphereActor.SetMapper(sphereMapper)

    #     sphereRenderer.AddActor(sphereActor)
    #     sphereRenderer.ResetCamera()
    #     sphereRenderWindow.Render()

    #     self.getApplication().InvalidateCache(renderWindow)
    #     self.getApplication().InvalidateCache(sphereRenderWindow)
    #     self.getApplication().InvokeEvent('UpdateEvent')

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

    @exportRpc("viewport.mouse.zoom.wheel")
    def updateZoomFromWheel(self, event):
        if 'Start' in event["type"]:
            self.getApplication().InvokeEvent(vtkCommand.StartInteractionEvent)

        # MouseWheelForwardEvent: event["spinY"] < 0
        # MouseWheelBackwardEvent: event["spinY"] > 0
            
        viewId = int(event.get("view"))
        logging.info(f"view id: {viewId}")

        # Axial view
        if (viewId == 1):
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
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
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
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
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
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                
                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
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
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                
                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in sagittal view
                self.sphereWidgetSagittal.SetCenter(newPosition)
                # Translate lines in sagittal view
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
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
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
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
                self.blueLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())
                self.redLineSagittalActor.SetPosition(self.sphereWidgetSagittal.GetCenter())

                # Translate sphere widget in axial view
                self.sphereWidgetAxial.SetCenter(newPosition)
                # Translate lines in axial view
                self.greenLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                self.blueLineAxialActor.SetPosition(self.sphereWidgetAxial.GetCenter())
                # Translate a rotation point on green line in axial view
                translationInterval = [newPosition[i] - self.currentSphereWidgetCenter["axial"][i] for i in range(3)]
                self.sphereWidgetInteractionRotateGreenLineAxial.SetCenter([self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()[i] + translationInterval[i] for i in range(3)])
                self.currentSphereWidgetCenterRotateLinesAxial["green"] = self.sphereWidgetInteractionRotateGreenLineAxial.GetCenter()

                # Translate sphere widget in coronal view
                self.sphereWidgetCoronal.SetCenter(newPosition)
                # Translate lines in coronal view
                self.greenLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())
                self.redLineCoronalActor.SetPosition(self.sphereWidgetCoronal.GetCenter())

        self.currentSphereWidgetCenter["axial"] = self.sphereWidgetAxial.GetCenter()
        self.currentSphereWidgetCenter["coronal"] = self.sphereWidgetCoronal.GetCenter()
        self.currentSphereWidgetCenter["sagittal"] = self.sphereWidgetSagittal.GetCenter()

        self.getApplication().GetObjectIdMap().GetActiveObject("AXIAL_VIEW").Render()
        self.getApplication().GetObjectIdMap().GetActiveObject("CORONAL_VIEW").Render()
        self.getApplication().GetObjectIdMap().GetActiveObject("SAGITTAL_VIEW").Render()

        if 'End' in event["type"]:
            self.getApplication().InvokeEvent(vtkCommand.EndInteractionEvent)
    
    # @exportRpc("viewport.mouse.zoom.wheel")
    # def updateZoomFromWheel(self, event):
    #   # logging.info(event)
    #   if 'Start' in event["type"]:
    #     self.getApplication().InvokeEvent('StartInteractionEvent')

    #   renderWindow = self.getView(event['view'])
    #   if renderWindow and 'spinY' in event:
    #     zoomFactor = 1.0 - event['spinY'] / 10.0

    #     camera = renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
    #     fp = camera.GetFocalPoint()
    #     pos = camera.GetPosition()
    #     delta = [fp[i] - pos[i] for i in range(3)]
    #     camera.Zoom(zoomFactor)

    #     pos2 = camera.GetPosition()
    #     camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
    #     renderWindow.Modified()

    #   if 'End' in event["type"]:
    #     self.getApplication().InvokeEvent('EndInteractionEvent')
        
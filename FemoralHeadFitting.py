import os
import vtk
import slicer
import numpy as np
import requests
from slicer.ScriptedLoadableModule import *
import qt, ctk

# ----------------------------------------------
# Main Module Class
# ----------------------------------------------
class FemoralHeadFitting(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)  # ✅ Fixed parent class call
        parent.title = "Femoral Head Fitting"
        parent.categories = ["Orthopedic Analysis"]
        parent.dependencies = []
        parent.contributors = ["Somashekar"]
        parent.helpText = """This module fits a sphere using two fiducial points: one as the center and another on the surface."""
        parent.acknowledgementText = "Developed for medical AR applications."

# ----------------------------------------------
# GUI (Widget) Class
# ----------------------------------------------
class FemoralHeadFittingWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Fiducial Button
        self.fiducialButton = qt.QPushButton("Select Fiducial Points")
        self.fiducialButton.clicked.connect(self.placeFiducialPoints)
        self.layout.addWidget(self.fiducialButton)

        # Fit Sphere Button
        self.fitSphereButton = qt.QPushButton("Fit Sphere from Points")
        self.fitSphereButton.clicked.connect(self.fitSphereFromTwoPoints)
        self.layout.addWidget(self.fitSphereButton)

        # Send to Unity Button
        self.sendToUnityButton = qt.QPushButton("Send Coordinates to Unity")
        self.sendToUnityButton.clicked.connect(self.sendCoordinatesToUnity)
        self.layout.addWidget(self.sendToUnityButton)
        
        self.fiducialNode = None
        self.sphereCenter = None
        self.sphereRadius = None

    def placeFiducialPoints(self):
        """ Enables fiducial placement in the Markups module """
        self.fiducialNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "FemoralHeadPoints")
        slicer.modules.markups.logic().StartPlaceMode(1)  # 1 = persistent mode

    def fitSphereFromTwoPoints(self):
        """ Creates a sphere using the center and a surface point """
        if not self.fiducialNode:
            slicer.util.errorDisplay("No fiducial points found.")
            return

        numPoints = self.fiducialNode.GetNumberOfControlPoints()
        if numPoints != 2:
            slicer.util.errorDisplay("Please place exactly 2 fiducial points: one for the center and one on the surface.")
            return

        # Get the two fiducial points
        center = [0, 0, 0]
        surfacePoint = [0, 0, 0]
        self.fiducialNode.GetNthControlPointPosition(0, center)  # First point → Sphere Center
        self.fiducialNode.GetNthControlPointPosition(1, surfacePoint)  # Second point → Surface Point

        # Compute radius
        radius = np.linalg.norm(np.array(surfacePoint) - np.array(center))

        if radius <= 0:
            slicer.util.errorDisplay("Invalid radius. Check the selected points.")
            return

        # Store sphere data
        self.sphereCenter = center
        self.sphereRadius = radius

        # Create and display the sphere
        logic = FemoralHeadFittingLogic()
        logic.createSphere(center, radius)

    def sendCoordinatesToUnity(self):
        """ Sends sphere center and radius to Unity API """
        if self.sphereCenter is None or self.sphereRadius is None:
            slicer.util.errorDisplay("No sphere data available. Fit the sphere first.")
            return

        # Flip the Y-coordinate
        transformedCenter = [
            self.sphereCenter[0],
            -self.sphereCenter[1],  # Multiply Y by -1
            self.sphereCenter[2]
        ]

        # Prepare request data
        data = {
            "x": transformedCenter[0],
            "y": transformedCenter[1],
            "z": transformedCenter[2],
            "radius": self.sphereRadius
        }

        # API Endpoint
        url = "https://cobridge.vercel.app/api/coordinates"

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                slicer.util.infoDisplay(f"✅ Sent successfully: {data}")
                print(f"✅ Unity Response: {response.json()}")
            else:
                slicer.util.errorDisplay(f"❌ Failed to send: {response.status_code}")
        except Exception as e:
            slicer.util.errorDisplay(f"❌ Error sending data: {str(e)}")

# ----------------------------------------------
# Logic Class (Computations)
# ----------------------------------------------
class FemoralHeadFittingLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)

    def createSphere(self, center, radius):
        """ Creates a 3D sphere at the computed location """
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(*center)  # ✅ Unpack list values properly
        sphereSource.SetRadius(radius)
        sphereSource.SetThetaResolution(50)
        sphereSource.SetPhiResolution(50)
        sphereSource.Update()

        if sphereSource.GetOutput().GetNumberOfPoints() == 0:
            print("❌ Sphere generation failed!")
            return

        print(f"✅ Sphere created with {sphereSource.GetOutput().GetNumberOfPoints()} points")

        # Create Model Node
        sphereModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "FemoralHeadSphere")
        sphereModel.SetAndObservePolyData(sphereSource.GetOutput())

        # Create Display Node
        displayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
        displayNode.SetColor(1, 0, 0)  # RED for visibility
        displayNode.SetOpacity(1.0)  # Ensure it's fully visible
        sphereModel.SetAndObserveDisplayNodeID(displayNode.GetID())

        # Ensure UI updates
        slicer.app.processEvents()
        print("✅ Sphere successfully added to 3D scene")


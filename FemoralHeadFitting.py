import os
import vtk
import slicer
import numpy as np
import requests
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator
from slicer.ScriptedLoadableModule import *
import qt, ctk


class FemoralHeadFitting(ScriptedLoadableModule):
    """Main module class defining metadata for 3D Slicer"""
    
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Femoral Head Fitting"
        parent.categories = ["Orthopedic Analysis"]
        parent.dependencies = []
        parent.contributors = ["Somashekar"]
        parent.helpText = """This module segments the femur using TotalSegmentator and fits a sphere to the femoral head using two fiducial points."""
        parent.acknowledgementText = "Developed for medical AR applications."


class FemoralHeadFittingWidget(ScriptedLoadableModuleWidget):
    """UI for user interaction"""
    
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = FemoralHeadFittingLogic()

        # Load Dataset and Segment Femur Button
        self.segmentFemurButton = qt.QPushButton("Segment Femur using TotalSegmentator")
        self.segmentFemurButton.clicked.connect(self.segmentFemur)
        self.layout.addWidget(self.segmentFemurButton)

        # Fiducial Placement Button
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

    def segmentFemur(self):
        """Segments the femur using TotalSegmentator."""
        input_path = "C:\\Users\\paula\\OneDrive\\Desktop\\dataset6_CLINIC_0001_data.nii.gz"
        success, output_path = self.logic.segmentFemur(input_path)

        if success:
            slicer.util.infoDisplay(f"✅ Segmentation completed. Output saved at {output_path}")
        else:
            slicer.util.errorDisplay(f"❌ Error during segmentation: {output_path}")

    def placeFiducialPoints(self):
        """Enables fiducial point placement in Slicer."""
        self.fiducialNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "FemoralHeadPoints")
        slicer.modules.markups.logic().StartPlaceMode(1)  # Persistent mode

    def fitSphereFromTwoPoints(self):
        """Fits a sphere using two fiducial points."""
        if not self.fiducialNode:
            slicer.util.errorDisplay("No fiducial points found.")
            return

        numPoints = self.fiducialNode.GetNumberOfControlPoints()
        if numPoints != 2:
            slicer.util.errorDisplay("Please place exactly 2 fiducial points: one for the center and one on the surface.")
            return

        # Extract fiducial points
        center = [0, 0, 0]
        surfacePoint = [0, 0, 0]
        self.fiducialNode.GetNthControlPointPosition(0, center)
        self.fiducialNode.GetNthControlPointPosition(1, surfacePoint)

        # Compute sphere parameters
        success, sphereCenter, sphereRadius = self.logic.computeSphere(center, surfacePoint)
        if not success:
            slicer.util.errorDisplay("Invalid sphere parameters. Check the selected points.")
            return

        # Create sphere visualization
        self.logic.createSphere(sphereCenter, sphereRadius)

    def sendCoordinatesToUnity(self):
        """Sends computed sphere parameters to Unity."""
        success, response = self.logic.sendToUnity()
        if success:
            slicer.util.infoDisplay(f"✅ Data sent successfully: {response}")
        else:
            slicer.util.errorDisplay(f"❌ Error sending data: {response}")


class FemoralHeadFittingLogic:
    """Computational logic for segmentation, sphere fitting, and Unity communication."""

    def __init__(self):
        self.sphereCenter = None
        self.sphereRadius = None

    def segmentFemur(self, input_path):
        """Runs TotalSegmentator for femur segmentation."""
        output_path = os.path.join(slicer.app.temporaryPath, "segmented_femur.nii.gz")

        try:
            input_img = nib.load(input_path)
            output_img = totalsegmentator(input_img, task="bones") #, structures=["femur", "pelvis"]
            nib.save(output_img, output_path)
            return True, output_path
        except Exception as e:
            return False, str(e)

    def computeSphere(self, center, surfacePoint):
        """Computes sphere parameters from two fiducial points."""
        try:
            center = np.array(center)
            surfacePoint = np.array(surfacePoint)

            radius = np.linalg.norm(surfacePoint - center)
            if radius <= 0:
                return False, None, None

            self.sphereCenter = center.tolist()
            self.sphereRadius = radius
            return True, self.sphereCenter, self.sphereRadius
        except Exception as e:
            return False, None, None

    def createSphere(self, center, radius):
        """Creates a 3D sphere in Slicer."""
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(radius)
        sphereSource.SetThetaResolution(50)
        sphereSource.SetPhiResolution(50)
        sphereSource.Update()

        if sphereSource.GetOutput().GetNumberOfPoints() == 0:
            return False

        sphereModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "FemoralHeadSphere")
        sphereModel.SetAndObservePolyData(sphereSource.GetOutput())

        displayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
        displayNode.SetColor(1, 0, 0)  # Red
        displayNode.SetOpacity(1.0)
        sphereModel.SetAndObserveDisplayNodeID(displayNode.GetID())

        slicer.app.processEvents()
        return True

    def sendToUnity(self):
        """Sends sphere data to Unity API."""
        if self.sphereCenter is None or self.sphereRadius is None:
            return False, "No sphere data available."

        transformedCenter = [self.sphereCenter[0], -self.sphereCenter[1], self.sphereCenter[2]]

        data = {"x": transformedCenter[0], "y": transformedCenter[1], "z": transformedCenter[2], "radius": self.sphereRadius}
        url = "https://cobridge.vercel.app/api/coordinates"

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Failed: {response.status_code}"
        except Exception as e:
            return False, str(e)

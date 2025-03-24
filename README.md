# Femoral Head Fitting Module for 3D Slicer

## Overview

The **Femoral Head Fitting** module is a custom extension for [3D Slicer](https://www.slicer.org), designed to assist in orthopedic analysis by fitting a sphere to the femoral head of a 3D model. This module enables users to:

- Place two fiducial points on a 3D model to define the center and a surface point of the femoral head.
- Compute and visualize a 3D sphere based on these points.
- Send the sphere’s center coordinates (with Y-coordinate flipped for Unity compatibility) and radius to a Unity AR application via an API endpoint.

This tool is ideal for medical professionals, researchers, and developers working on medical augmented reality (AR) applications, preoperative planning, or educational tools.

---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
   - [Placing Fiducial Points](#placing-fiducial-points)
   - [Fitting the Sphere](#fitting-the-sphere)
   - [Sending Coordinates to Unity](#sending-coordinates-to-unity)
3. [Module Architecture](#module-architecture)
4. [Dependencies](#dependencies)
5. [Contributing](#contributing)
6. [License](#license)
7. [Acknowledgements](#acknowledgements)

---

## Installation

To install and use the **Femoral Head Fitting** module in 3D Slicer, follow these steps:

1. **Install 3D Slicer:**
   - Download and install the latest stable version of 3D Slicer from [https://www.slicer.org](https://www.slicer.org).

2. **Clone the Repository:**
   - Clone this GitHub repository to your local machine:
     ```bash
     git clone https://github.com/btp-hvision/segmentation.git
     ```

3. **Load the Module in 3D Slicer:**
   - Open 3D Slicer.
   - Enable Developer Mode:
     - Navigate to **Edit** > **Application Settings** > **Modules** tab and check **Enable Developer Mode**.
   - Open the Python Interactor:
     - Go to **View** > **Python Interactor**.
   - Load the script:
     - In the Python Interactor, run:
       ```python
       slicer.util.loadScriptedModule("path/to/FemoralHeadFitting.py")
       ```
     - Replace `"path/to/FemoralHeadFitting.py"` with the actual file path to the `FemoralHeadFitting.py` script.

4. **Alternative Installation:**
   - Move the `FemoralHeadFitting.py` file to the Slicer Modules directory (e.g., `~/Slicer-Modules/`), then restart 3D Slicer. The module will appear under **Orthopedic Analysis** in the Modules dropdown.

---

## Usage

After loading the module, access it via the **Modules** dropdown in 3D Slicer: **Orthopedic Analysis** > **Femoral Head Fitting**. The interface includes three main buttons:

### Placing Fiducial Points

1. Click the **Select Fiducial Points** button.
2. Place exactly **two fiducial points** on the 3D model:
   - **First Point:** The approximate center of the femoral head.
   - **Second Point:** Any point on the surface of the femoral head.
3. These points are stored as a `vtkMRMLMarkupsFiducialNode` named "FemoralHeadPoints" in the scene.

### Fitting the Sphere

1. Click the **Fit Sphere from Points** button.
2. The module:
   - Verifies that exactly two fiducial points are placed.
   - Computes the sphere’s radius as the Euclidean distance between the center (first point) and the surface point (second point).
   - Generates a 3D sphere using VTK, centered at the first point with the calculated radius.
3. The sphere is displayed in the 3D scene as a red, fully opaque model named "FemoralHeadSphere".

**Note:** If fewer or more than two points are placed, or if the radius is invalid (≤ 0), an error message will appear.

### Sending Coordinates to Unity

1. Click the **Send Coordinates to Unity** button.
2. The module:
   - Flips the Y-coordinate of the sphere’s center. (This can be adjusted relative to the model)
   - Prepares a JSON payload with the transformed center (`x`, `y`, `z`) and radius.
   - Sends the data to the API endpoint: `https://cobridge.vercel.app/api/coordinates`.
3. A success message (✅) appears if the data is sent successfully (HTTP 200), otherwise an error message (❌) is displayed with the status code or exception details.

**Example Payload:**
```json
{
  "x": 10.0,
  "y": -5.0,
  "z": 2.0,
  "radius": 15.0
}
```

---

## Module Architecture

The module is implemented in Python and consists of three main classes:

1. **`FemoralHeadFitting` (ScriptedLoadableModule):**
   - Defines metadata: Title, Category, Contributors, Help Text, Acknowledgement

2. **`FemoralHeadFittingWidget` (ScriptedLoadableModuleWidget):**
   - Manages the GUI with three buttons:
     - **Select Fiducial Points:** Initiates fiducial placement via the Markups module.
     - **Fit Sphere from Points:** Triggers sphere computation and visualization.
     - **Send Coordinates to Unity:** Sends sphere data to the Unity API.
   - Stores fiducial node, sphere center, and radius as instance variables.

3. **`FemoralHeadFittingLogic` (ScriptedLoadableModuleLogic):**
   - Handles computations and visualization:
     - **`createSphere`:** Uses `vtk.vtkSphereSource` to generate a sphere with 50x50 theta/phi resolution, adds it to the scene as a red model.

The module leverages:
- **VTK** for 3D sphere rendering.
- **NumPy** for radius computation.
- **Requests** for API communication.

---

## Dependencies

The module requires the following dependencies, most of which are bundled with 3D Slicer:
- **3D Slicer** (latest stable version)
- **VTK** (included with 3D Slicer)
- **NumPy** (included with 3D Slicer)
- **Requests** (for HTTP requests to Unity API)

If the `requests` library is missing, install it within Slicer’s Python environment:
```python
slicer.util.pip_install("requests")
```

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature or bugfix branch:
   ```bash
   git checkout -b my-feature-branch
   ```
3. Commit your changes with clear messages:
   ```bash
   git commit -m "Add feature X"
   ```
4. Push to your fork and submit a pull request:
   ```bash
   git push origin my-feature-branch
   ```

Please include detailed descriptions in your pull requests and adhere to the existing code style.

---

## License

This project is licensed under the [MIT License](LICENSE). See the `LICENSE` file for details.

---

## Acknowledgements

- Thanks to the 3D Slicer community for providing a robust platform and resources.

---

This README provides a complete guide to installing, using, and contributing to the **Femoral Head Fitting** module. For questions or issues, please open a ticket on the GitHub repository.

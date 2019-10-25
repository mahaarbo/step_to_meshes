# STEP TO MESHES
This script converts the shapes/parts in a STEP file to meshes for use in rViz, Gazebo, or similar. 

## USAGE
Read the help: `python step_to_meshes.py -h`.

Places all meshes in a `meshes` folder in the current working directory. 

## File formats
Can export `STL`, `AMF`, `DAE`, `OBJ`, basically the script can take whatever FreeCAD can open, and export whatever mesh meshlabserver can support. 

## Troubleshooting
FreeCAD is still not a very stable CAD system, so always double check your results to see if the origin is as expected, and FreeCAD has managed to create the right BRep bodies. 
If it has failed, you can run the script 'step_to_meshes_fusion360.py' in Autodesk Fusion 360 to get the simple and full meshes.
No convex hull is calculated with the fusion360 script.

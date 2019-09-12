# STEP TO MESHES
This script converts the shapes/parts in a STEP file to meshes for use in rViz, Gazebo, or similar. 

## USAGE
Read the help: `python step_to_meshes.py -h`.

Places all meshes in a `meshes` folder in the current working directory. 

## File formats
Can export `STL`, `AMF`, `DAE`, `OBJ`, basically the script can take whatever FreeCAD can open, and export whatever mesh meshlabserver can support. 

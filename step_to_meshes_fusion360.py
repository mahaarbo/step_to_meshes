#Author-Mathias Hauan Arbo
#Description-Convert all the components in a step file to meshes.

import adsk.core, adsk.fusion, adsk.cam, traceback
import os.path
from  os import mkdir
import csv
import math

def rotation_to_axis_angle(r00, r01, r02,
                           r10, r11, r12,
                           r20, r21, r22):
    """Takes a transform and produces the axis angle associated with the rotation.
    returns: angle, axis_x, axis_y, axis_z"""
    # based on http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToAngle/index.htm
    epsilon = 0.00001
    if abs(r01-r10) < epsilon and abs(r02-r20) < epsilon and abs(r12 - r21) < epsilon:
        # Singularity
        if abs(r01+r10 < 2*epsilon) and abs(r02 + r20) < 2*epsilon and abs(r12 + r21) < epsilon and abs(r00+r11+r22-3) < epsilon:
            # Zero angle singularity
            return 0.,1.,0.,0.
        else:
            # 180 degree angle singularity
            xx = (r00+1)/2.
            yy = (r11+1)/2.
            zz = (r22+1)/2.
            xy = (r01+r10)/4.
            xz = (r02+r20)/4.
            yz = (r12+r21)/4.
            if ((xx > yy) and (xx > zz)):
                if (xx< epsilon):
                    x = 0.
                    y = 0.7071
                    z = 0.7071
                else:
                    x = math.sqrt(xx)
                    y = xy/x
                    z = xz/x
            elif (yy > zz):
                if (yy< epsilon):
                    x = 0.7071
                    y = 0.
                    z = 0.7071
                else:
                    y = math.sqrt(yy)
                    x = xy/y
                    z = yz/y
            else:
                if (zz< epsilon):
                    x = 0.7071
                    y = 0.7071
                    z = 0.0
                else:
                    z = math.sqrt(zz)
                    x = xz/z
                    y = yz/z
            return math.pi, x, y, z
    s = math.sqrt((r21 - r12)*(r21 - r12) + (r02 - r20)*(r02 - r20) + (r10 - r01)*(r10 - r01))
    if (abs(s) < epsilon):
        s = 1
    angle = math.acos(( r00 + r11 + r22 - 1)/2)
    x = (r21 - r12)/s
    y = (r02 - r20)/s
    z = (r10 - r01)/s
    return angle, x, y, z


def transform_to_xyz_angle_axis(transf):
    """Takes a transform and produces the displacement and quaternion associated with it"""
    angle, axis_x, axis_y, axis_z = rotation_to_axis_angle(transf.getCell(0,0), transf.getCell(0,1), transf.getCell(0,2),
                                                           transf.getCell(1,0), transf.getCell(1,1), transf.getCell(1,2),
                                                           transf.getCell(2,0), transf.getCell(2,1), transf.getCell(2,2))
    x, y, z = transf.getCell(0,3), transf.getCell(1,3), transf.getCell(2,3)
    return x, y, z, angle, axis_x, axis_y, axis_z


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeDocument
        design = adsk.fusion.Design.cast(product.design)
        # Figure out which folder the person wants the meshes in
        folderDlg = ui.createFolderDialog()
        folderDlg.title = "Folder to save the mesh folder to"
        dlgResult = folderDlg.showDialog()
        if dlgResult == adsk.core.DialogResults.DialogOK:
            meshpath = folderDlg.folder
            # Get the root component (in which everything is made)
            rootComponent = design.rootComponent
            # Get all components
            components = design.allComponents
            exportMgr = design.exportManager
            nComponents = len(components)
            # Create progressbar
            for component in components:
                # Count the number of occurrences
                occurrences = rootComponent.allOccurrencesByComponent(component)
                nOccurrences = len(occurrences)
                # No occurrence? Then we skip this
                if nOccurrences == 0:
                    continue
                # Make sure the component folder exists
                componentpath = os.path.join(meshpath, component.name)
                if not os.path.exists(componentpath):
                    os.mkdir(componentpath)
                # Create the placements.csv file
                placepath = os.path.join(componentpath, "placements.csv")
                with open(placepath, "w") as csvfile:
                    csvwrtr = csv.writer(csvfile, delimiter=",")
                    csvwrtr.writerow(["Label", "x [m]", "y [m]", "z [m]", "axis_x", "axis_y", "axis_z", "angle"])
                    for occ in occurrences:
                        # Get xyz and axis-angle 
                        x, y, z, angle, axis_x, axis_y, axis_z = transform_to_xyz_angle_axis(occ.transform)
                        csvwrtr.writerow([occ.name.replace(":","__"),
                                          x,y,z,
                                          axis_x,axis_y,axis_z,angle])
                        

                # Create the simple.stl
                stlOptions = exportMgr.createSTLExportOptions(component, os.path.join(componentpath, "simple"))
                stlOptions.sendToPrintUtility = False
                stlOptions.meshRefinement = 2  # 0 = High, 1 = Medium, 2 = Low mesh refinement
                exportMgr.execute(stlOptions)
                # Create the full.stl
                stlFullOptions = exportMgr.createSTLExportOptions(component, os.path.join(componentpath, "full"))
                stlFullOptions.sendToPrintUtility = False
                stlFullOptions.meshRefinement = 1
                exportMgr.execute(stlFullOptions)
        else:
            exit
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

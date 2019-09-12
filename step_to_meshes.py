#!/usr/bin/env python

# Author: Mathias Hauan Arbo
# Date: 25. September, 2017
# License: See separate LICENSE file

""" Convert step files to meshes using freecad. Simplifies the mesh using
meshlab.  Also makes convex hulls, and can run arbitrary meshlabscripts using
meshlabserver. Originally intended to create meshes for URDFs, which is why it
produces a \"/meshes/\" folder. """

import sys
import csv
import argparse
import subprocess
import os
try:
    import FreeCAD
except ImportError:
    if not os.path.exists("/usr/lib/freecad/lib/"):
        # To cheat python 2/3 compatible input/output I'll just use
        # sys.stdout/stdin directly
        sys.stdout.write("FreeCAD not found at /usr/lib/freecad/lib/. Please"
                         " specify path to freecad.\n")
        # Python 2/3 compatible input handling
        FREECADPATH = sys.stdin.readline()
        if FREECADPATH[-1] == "\n":
            FREECADPATH = FREECADPATH[:-1]
    else:
        # Ubuntu standard placement
        FREECADPATH = "/usr/lib/freecad/lib/"
    sys.path.append(FREECADPATH)
    import FreeCAD
import Mesh
import importDAE
import importOBJ
import Import as freecadimport  # Very unfortunate module name


def executeMeshlabScript(imesh_path, script_path, omesh_path=None,
                         optargs="-om vn fn", verbose=False):
    """Executes `meshlabserver -i imesh_path -s script_path -o
    omesh_path optargs.  If unspecified, omesh_path is in imesh_folder
    and is named script_name.fileextension.
    Returns the path to the resulting mesh.
    """
    # Path handling
    script_name = os.path.splitext(os.path.split(script_path)[-1])[0]
    imesh_file = os.path.split(imesh_path)[-1]
    ext = os.path.splitext(imesh_file)[-1]
    imeshfolder_path = os.path.split(imesh_path)[0]
    if not omesh_path:
        omesh_path = os.path.join(imeshfolder_path, script_name + ext)
    omeshfolder_path = os.path.split(omesh_path)[0]
    if not os.path.exists(omeshfolder_path):
        os.makedirs(omeshfolder_path)
    # Calling the meshlabscript
    if verbose:
        temp = subprocess.check_output("meshlabserver -i " + imesh_path
                                       + " -o " + omesh_path + " "
                                       + optargs + " -s " + script_path,
                                       shell=True)
        sys.stdout.write(temp)
    else:
        deadpipe = open(os.devnull, "w")
        subprocess.call("meshlabserver -i " + imesh_path + " -o " + omesh_path
                        + " " + optargs + " -s " + script_path,
                        shell=True, stderr=deadpipe, stdout=deadpipe)
    return omesh_path


def sanitizeAndPlace(func):
    """Sanitizes the output mesh path and places the object in local or
    global frame."""
    def function_wrapper(obj, omesh_path=None,
                         use_global_frame=True):
        if not omesh_path:
            omeshfolder_path = os.path.join("./meshes/", obj.Label)
            omesh_path = os.path.join(omeshfolder_path, "full")
        else:
            omeshfolder_path = os.split(omesh_path)[0]
        if not os.path.exists(omeshfolder_path):
            os.makedirs(omeshfolder_path)
        prev_pl = obj.Placement
        if not use_global_frame:
            pl = getGlobalPlacement(obj)
            obj.Placement = pl.inverse().multiply(obj.Placement)
        res = func(obj, omesh_path)
        obj.Placement = prev_pl
        return res
    return function_wrapper


def getGlobalPlacement(obj):
    """Get global placement in a way that works with FreeCAD version
    0.16 and beyond.
    """
    if hasattr(obj, "getGlobalPlacement"):
        # We are in FreeCAD > 0.16
        pl = obj.getGlobalPlacement()
    else:
        # We are in FreeCAD 0.16 or something
        pl = obj.Placement()
    return pl


def savePlacements(labelplacementpairs, csvfilename):
    """Saves the placements in a list of placements to a csvfile."""
    odir, ofilename = os.path.split(csvfilename)
    if not os.path.exists(odir):
        os.makedirs(odir)
    with open(csvfilename, "wb") as ofile:
        csvw = csv.writer(ofile, delimiter=",")
        csvw.writerow(["Label",
                       "x [m]", "y [m]", "z [m]",
                       "axis_x", "axis_y", "axis_z",
                       "angle"])
        for pair in labelplacementpairs:
            label = pair[0]
            pl = pair[1]
            pos, R = pl.Base, pl.Rotation
            csvw.writerow([label,
                           pos.x*1e-3, pos.y*1e-3, pos.z*1e-3,
                           R.Axis.x, R.Axis.y, R.Axis.z,
                           R.Angle])


@sanitizeAndPlace
def exportAMF(obj, omesh_path):
    """
    Export ./\"meshfolder_path\"/\"Label\"/full.amf from the FreeCAD object.
    Uses Mesh module and returns path to the AMF.
    """
    omesh_path += ".amf"
    Mesh.export([obj], omesh_path)
    return omesh_path


@sanitizeAndPlace
def exportDAE(obj, omesh_path):
    """
    Export ./\"meshfolder_path\"/\"Label\"/full.dae from the FreeCAD object.
    Uses importDAE module and returns path to the DAE.
    """
    omesh_path += ".dae"
    importDAE.export([obj], omesh_path)
    return omesh_path


@sanitizeAndPlace
def exportOBJ(obj, omesh_path):
    """
    Export ./\"meshfolder_path\"/\"Label\"/full.obj from the FreeCAD object.
    Uses importOBJ module and returns path to the obj.
    """
    omesh_path += ".obj"
    importOBJ.export([obj], omesh_path)
    return omesh_path


@sanitizeAndPlace
def exportSTL(obj, omesh_path):
    """
    Export ./\"meshfolder_path\"/\"Label\"/full.stl from the FreeCAD object.
    Uses Mesh module and returns path to the STL.
    """
    omesh_path += ".stl"
    Mesh.export([obj], omesh_path)
    return omesh_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert step files into meshes. Exports all "
                    "parts as separate meshes, either with origin"
                    " in their part-local origin, or with respect"
                    " to the \"global\" design origin.")
    parser.add_argument("cadfile",
                        help="Supports all formats FreeCAD supports.")
    parser.add_argument("-ns", "--num-simplify",
                        help="Number of times to run the simplifier "
                             "(default: 10).",
                        default=10, type=int,
                        required=False)
    parser.add_argument("-nc", "--num-chull",
                        help="Generate convex hull, then simplify nc-1 times."
                             " (default: 10)",
                        default=10, type=int,
                        required=False)
    parser.add_argument("-ext", "--file-extension",
                        help="Default: \".stl\", others: \".obj\", \".dae\","
                             " \".amf\".",
                        default=".stl",
                        required=False)
    parser.add_argument("-g", "--use-design-global-origin",
                        help="Flag to use global origin.",
                        required=False,
                        action="store_true")
    parser.add_argument("-v", "--verbose",
                        help="Print meshlabscript outputs.",
                        required=False,
                        action="store_true")
    args = parser.parse_args()
    # Open file
    doc = FreeCAD.newDocument("temp")
    FreeCAD.setActiveDocument("temp")
    freecadimport.insert(args.cadfile, "temp")

    # Gather the unique shapes, and clone parts
    unique_objs = []
    parts = {}
    num_objs = 0
    for obj in doc.Objects:
        new_shape = True
        if obj.TypeId == "Part::Feature":
            num_objs += 1
            for uobj in unique_objs:
                if uobj.Shape.isPartner(obj.Shape):
                    new_shape = False
                    parts[uobj.Label]["placements"] += [[obj.Label,
                                                         obj.Placement]]
            if new_shape:
                unique_objs.append(obj)
                parts[obj.Label] = {
                    "obj": obj,
                    "placements": [[obj.Label, obj.Placement]]
                }
    sys.stdout.write("Found " + str(num_objs) + " where " +
                     str(len(unique_objs)) + " are unique.\n")
    sys.stdout.write("Mesh generation:\n")
    globpl = args.use_design_global_origin
    for uobj in unique_objs:
        sys.stdout.write(uobj.Label+":\n")
        # Export full mesh
        if "stl" in args.file_extension.lower():
            meshpath = exportSTL(uobj, use_global_frame=globpl)
        elif "obj" in args.file_extension.lower():
            meshpath = exportOBJ(uobj, use_global_frame=globpl)
        elif "dae" in args.file_extension.lower():
            meshpath = exportDAE(uobj, use_global_frame=globpl)
        elif "amf" in args.file_extension.lower():
            meshpath = exportAMF(uobj, use_global_frame=globpl)
        else:
            raise ValueError("Unknown file extension specified")
        sys.stdout.write("\t-Mesh generated\n")
        # Export placements
        meshdir = os.path.split(meshpath)[0]
        csvfilename = os.path.join(meshdir, "placements.csv")
        savePlacements(parts[uobj.Label]["placements"], csvfilename)
        nclones = len(parts[uobj.Label]["placements"])
        if nclones > 1:
            sys.stdout.write("\t-" + str(nclones-1) + " clones placed\n")
        # Convex Hull
        cwd = os.getcwd()
        if args.num_chull > 0:
            chullpath = executeMeshlabScript(meshpath,
                                             os.path.join(cwd, "chull.mlx"),
                                             verbose=args.verbose)
            for i in range(1, args.num_chull):
                executeMeshlabScript(chullpath,
                                     os.path.join(cwd, "simple.mlx"),
                                     omesh_path=chullpath,
                                     verbose=args.verbose)
            sys.stdout.write("\t-Generated convex hull\n")
        # Simplify base mesh
        if args.num_simplify > 0:
            simplepath = executeMeshlabScript(meshpath,
                                              os.path.join(cwd, "simple.mlx"),
                                              verbose=args.verbose)
            for i in range(1, args.num_simplify):
                executeMeshlabScript(simplepath,
                                     os.path.join(cwd, "simple.mlx"),
                                     simplepath,
                                     verbose=args.verbose)
            sys.stdout.write("\t-Generated simplified model\n")
    sys.stdout.write("Note: Check chull and simplified meshes for issues!\n")

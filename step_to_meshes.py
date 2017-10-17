#!/bin/python
#Author: Mathias Hauan Arbo
#Date: 25. September, 2017
"""
Convert step files to meshes using freecad. Simplifies the stl using meshlab.
Also makes convex hulls, and can run arbitrary meshlabscripts using meshlabserver.
"""
import sys
FREECADPATH = "/usr/lib/freecad/lib/" #Ubuntu repo standard
DEBUGPRINT = False #be very verbose
sys.path.append(FREECADPATH)
import FreeCAD
import os
import subprocess
import Mesh
import csv
import json

def run_script_on_mesh(imesh_path, script_path, omesh_path=None, optargs="-om vn fn", verbose=False):
    """
    Executes meshlabserver -i imesh_path -s script_path -o omesh_path optargs.
    If unspecified, omesh_path is in imesh_folder and is named script_name.stl.
    """
    script_name = os.path.splitext(os.path.split(script_path)[-1])[0]
    imesh_file = os.path.split(imesh_path)[-1]
    imeshfolder_path = os.path.split(imesh_path)[0]
    if not omesh_path:
        omesh_path = os.join(imeshfolder_path, script_name+".stl")
    omeshfolder_path = os.path.split(omesh_path)[0]
    if not os.path.exists(omeshfolder_path):
        os.makedirs(omeshfolder_path)
    if verbose:
        temp = subprocess.check_output("meshlabserver -i " + imesh_path + " -o " + omesh_path + " "+optargs + " -s " + script_path, shell=True)
        sys.stdout.write(temp)
        
    else:
        deadpipe = open(os.devnull,'w')
        subprocess.call("meshlabserver -i " + imesh_path + " -o " + omesh_path + " "+optargs + " -s " + script_path,shell=True,stdout=deadpipe,stderr=deadpipe)
        deadpipe.close()
    
def make_STL(obj, omesh_path=None, placement="local"):
        """
        Make \"meshfolder_path\"/\"Label\"/full.stl from the object. Uses Shape module of FreeCAD.
        returns omesh_path
        Note: STL's origin is placed at Shape's \"origin\".
        TODO: Allow origin transformation
        """
        if not omesh_path:
            omeshfolder_path = os.path.join("./meshes/", obj.Label)
            omesh_path = os.path.join(omeshfolder_path, "full.stl")
        else:
            omeshfolder_path = os.split(omesh_path)[0]
        if not os.path.exists(omeshfolder_path):
            os.makedirs(omeshfolder_path)

        if placement is "local":
            prev_pl = obj.Placement
            obj.Placement = obj.Placement.inverse().multiply(obj.Placement)
        elif isinstance(placement, FreeCAD.Placement):
            obj.Placement = placement
            placement2csv(obj.Placement, os.path.join(omeshfolder_path, "newplacement.csv"))
        Mesh.export([obj],omesh_path)
        obj.Placement = prev_pl
        return omesh_path
    
def make_OBJ(obj, omesh_path=None, placement="local"):
    """
    Make \"meshfolder_path\"/\"Label\"/full.obj from the object. Uses Shape module of FreeCAD.
    returns omesh_path
    """
    if not omesh_path:
        omeshfolder_path = os.path.join("./meshes/", obj.Label)
        omesh_path = os.path.join(omeshfolder_path, "full.stl")
    else:
        omeshfolder_path = os.split(omesh_path)[0]
    if not os.path.exists(omeshfolder_path):
        if DEBUGPRINT:
            sys.stdout.write("Creating "+omeshfolder_path+"\n")
        os.makedirs(omeshfolder_path)
    #Ideally this uses custom transformation, and isn't desctructive. But whatever.
    if placement is "local":
        obj.Placement = obj.Placement.inverse().multiply(obj.Placement)
        
    elif isinstance(placement, FreeCAD.Placement):
        obj.Placement = placement

    if DEBUGPRINT:
        sys.stdout.write("Creating "+omesh_path+"\n")
    obj.Shape.exportObj(omesh_path)
    return omesh_path
    
def make_simplified_STL(imesh_path, script_path = "./simplifymesh.mlx", omesh_path=None, n_iterations = 1, verbose=False):
    """
    From mesh_path, make \"simple.stl\" in the same folder using \"simplifymesh.mlx\".
    Iterates the meshlab script \"n_iterations\" times.
    """
    meshfolder_path, mesh_file = os.path.split(imesh_path)
    if not omesh_path:
        omesh_path = os.path.join(meshfolder_path, "simple.stl")
    if DEBUGPRINT:
        sys.stdout.write("Simplifying "+imesh_path+", "+str(n_iterations)+" iterations. Out: "+omesh_path+"\n")
    run_script_on_mesh(imesh_path = imesh_path,
                       script_path = script_path,
                       omesh_path = omesh_path)
    for i in xrange(1,n_iterations):
        if DEBUGPRINT:
            sys.stdout.write(str(i))
        run_script_on_mesh(imesh_path = omesh_path,
                          script_path = script_path,
                          omesh_path = omesh_path,
                          verbose = verbose)
    if DEBUGPRINT:
        sys.stdout.write("\n")
    return omesh_path

def make_convex_hull(imesh_path, script_path = "./chull.mlx", omesh_path = None, verbose = False):
    """
    From mesh_path, make \"chull.stl\" in the same folder using \"chull.mlx\".
    Does not perform simplification.
    """
    meshfolder_path, mesh_file = os.path.split(imesh_path)
    if not omesh_path:
        omesh_path = os.path.join(meshfolder_path, "chull.stl")
    if DEBUGPRINT:
        sys.stdout.write("Creating convex hull of "+imesh_path)
    run_script_on_mesh(imesh_path = imesh_path,
                      script_path = script_path,
                      omesh_path = omesh_path,
                      verbose = verbose)
    return omesh_path

def get_unique_objects(fc_doc):
    """
    Return a list of unique objects in FreeCAD document. Objects are unique if they have a unique label.
    """
    unique_objects = []
    for obj in fc_doc.Objects:
        if not obj.Label in (o.Label for o in unique_objects):
            unique_objects.append(obj)
    if DEBUGPRINT:
        sys.stdout.write("Found " + str(len(unique_objects)) +" unique objects\n")
    return unique_objects


def placement2csv(placements, csvfilename, writingmode="wb"):
    import csv
    odir, ofilename = os.path.split(csvfilename)
    if not type(placements) is list:
        placements = [placements]
    if not os.path.exists(odir):
        os.makedirs(odir)
    with open(csvfilename, writingmode) as plcsv:
        csvwriter = csv.writer(plcsv, delimiter = ",")
        for pl_ind, pl in enumerate(placements):
            mat = pl.toMatrix()
            csvwriter.writerow(["Placement"])
            csvwriter.writerow(["Base", pl.Base.x, pl.Base.y, pl.Base.z])
            csvwriter.writerow(["Axis", pl.Rotation.Axis.x, pl.Rotation.Axis.y, pl.Rotation.Axis.z])
            csvwriter.writerow(["Angle", pl.Rotation.Angle])
            csvwriter.writerow(["Matrixr1", mat.A11, mat.A12, mat.A13, mat.A14])
            csvwriter.writerow(["Matrixr2", mat.A21, mat.A22, mat.A23, mat.A24])
            csvwriter.writerow(["Matrixr3", mat.A31, mat.A32, mat.A33, mat.A34])
            csvwriter.writerow(["Matrixr4", mat.A41, mat.A42, mat.A43, mat.A44])
    return csvfilename
        

def csv2placement(csvfilename):
    import FreeCAD
    with open(csvfilename) as placementcsv:
        csvreader  = csv.reader(placementcsv, delimiter=",")
        placements =[]
        for row in csvreader:
            if row[0] == "Placement_Index":
                placements.append(FreeCAD.Placement())
            elif row[0] == "Base":
                placements[-1].Base.x = float(row[1])
                placements[-1].Base.y = float(row[2])
                placements[-1].Base.z = float(row[3])
            elif row[0] == "Axis":
                placements[-1].Rotation.Axis.x = float(row[1])
                placements[-1].Rotation.Axis.y = float(row[2])
                placements[-1].Rotation.Axis.z = float(row[3])
            elif row[0] == "Angle":
                placements[-1].Rotation.Angle = float(row[1])
    return placements


def mesh2luacomp(oluafile, propertiesdict, deployer='depl'):
    """Write a lua viz_marker file for the mesh.
    Activity frequency is taken from propertiesdict[\"lifetime\"]."""

    oluadir, olua = os.path.split(oluafile)
    olua, temp = os.path.splitext(olua)
    if not os.path.exists(oluadir):
        os.makedirs(oluadir)
    #Start writing the luacode
    luacode = deployer+':loadComponent("'+olua+'_viz","Viz_Marker")\n'
    luacode += olua+'_viz = '+deployer+':getPeer("'+olua+'_viz")\n'
    for key, value in propertiesdict.items():
        if value == "true":
            luacode += olua + '_viz:getProperty("' + key + '"):set(true)\n'
        elif value == "false":
            luacode += olua + '_viz:getProperty("' + key + '"):set(false)\n'
        else:
            if type(value) is str or type(value) is unicode:
                luacode += olua + '_viz:getProperty("' + key + '"):set("'+ str(value) +'")\n'
            else:
                luacode += olua + '_viz:getProperty("' + key + '"):set(' + str(value) + ')\n'
    luacode += olua + '_viz:configure()\n'
    luacode += deployer + ':setActivity("' + olua + '_viz", ' + str(propertiesdict["lifetime"]) + ', 50, rtt.globals.ORO_SCHED_RT)\n'
    luacode += deployer + ':stream("' + olua + '_viz.output", ros:topic("/visualization_marker"))\n'
    luacode += olua + '_viz:start()\n'
    luacode += olua + '_viz_loc = rttlib.port_clone_conn(' + olua + '_viz:getPort("input1"))\n'
    with open(oluafile,'wb') as ofile:
        ofile.write(luacode)
    return oluafile
def placement2list(placement):
    mat = placement.toMatrix()
    return [[mat.A11, mat.A12, mat.A13, mat.A14],
            [mat.A21, mat.A22, mat.A23, mat.A24],
            [mat.A31, mat.A32, mat.A33, mat.A34],
            [mat.A41, mat.A42, mat.A43, mat.A44]]

if __name__=="__main__":
    #Argument handling
    import argparse
    import Import as fcimp #What a terribly ugly and confusing module name
    parser = argparse.ArgumentParser(description="Convert step files into meshes.")
    parser.add_argument("cadfile",
                        help="Supported formats: .stp")
    parser.add_argument("-partlocalframe",
                        help="Sets the coordinate frames to local of the part",
                        action="store_true")
    parser.add_argument("-nsimplify",
                        help="Number of iterations the simplifier runs (default 10)",
                        default=10,type=int)
    parser.add_argument("-nchull",
                        help="Number of iterations the simplifier runs after convex hull(default 10)",type=int)
    parser.add_argument("-wlua",
                        help="create lua components for spawning visualization markers",
                        action="store_true")
    
    args = parser.parse_args()

    doc = FreeCAD.newDocument("temp")
    FreeCAD.setActiveDocument("temp")
    fcimp.insert(args.cadfile,"temp")
    
    if args.partlocalframe:
        placement = "local"
    else:
        placement = ""
    obj_found = {}
    scaling = 0.01 #Meshfiles are in mm
    properties_viz = {"nrofmarkers":1,
                      "frameid":"world",
                      "type":10,
                      "scalex":scaling,
                      "scaley":scaling,
                      "scalez":scaling,
                      "red":0.51,
                      "green":0.51,
                      "blue":0.53,
                      "alpha":1.0,
                      "lifetime":0.01,
                      "mesh_resource":"package://my_etasl_test/meshes/compressor_local/",
                      "resend":"true"
                      }
    for obj in doc.Objects:
        #Make the mesh if it is unique
        if not obj.Label in obj_found.keys():
            stl_path = make_STL(obj, placement = placement)
            simple_path = make_simplified_STL(stl_path,
                                              n_iterations = args.nsimplify)
            chull_path = make_convex_hull(stl_path,
                                          verbose=False)
            make_simplified_STL(chull_path,
                                omesh_path = chull_path,
                                n_iterations = args.nchull)
            obj_found[obj.Label] = 0
            print "Completed mesh for "+obj.Label
            oldplacement = obj.Placement
            obj.Placement = FreeCAD.Placement()
            with open(os.path.join("./meshes", obj.Label, "properties.json"), "ab") as partprops:
                partprops.writerow
        
        #Make or append the placement csv if localframes
        if args.partlocalframe:
            placement2csv(obj.Placement,
                          os.path.join("./meshes/",obj.Label, "placement.csv"),
                          writingmode="ab")
            obj_found[obj.Label] = obj_found[obj.Label] + 1
            print "Wrote/appended placement for "+obj.Label+", #"+str(obj_found[obj.Label])
            
        #Write the luacode for it
        if args.wlua:
            base_mesh_resource = properties_viz["mesh_resource"]
            properties_viz["mesh_resource"] = os.path.join(properties_viz["mesh_resource"],obj.Label,"simple.stl")
            if obj_found[obj.Label]==1:
                oluafile = os.path.join("./meshes", "viz_script", obj.Label + ".lua")
            else:
                oluafile = os.path.join("./meshes", "viz_script", obj.Label + str(obj_found[obj.Label]) + ".lua")
            mesh2luacomp(oluafile, properties_viz)
            properties_viz["mesh_resource"] = base_mesh_resource
            print "Made lua file for "+obj.Label+", #"+str(obj_found[obj.Label])
        
        

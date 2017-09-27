#!/bin/python

#Author: Mathias Hauan Arbo
#Date: 25. September, 2017

import sys
FREECADPATH = "/usr/lib/freecad/lib/" #Ubuntu repo standard
DEBUGPRINT = True #be very verbose
sys.path.append(FREECADPATH)
import FreeCAD
import Import as fcimp #What a terribly ugly and confusing module name
import os
import subprocess

def run_script_on_STL(imesh_path, script_path, omesh_path=None, optargs="-om vn fn", verbose=False):
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
        if DEBUGPRINT:
            sys.stdout.write("Creating "+omesh_path+"\n")
        os.makedirs(omeshfolder_path)
    if DEBUGPRINT: 
        sys.stdout.write("Script "+script_path+" on "+imesh_path+" to "+omesh_path+"\n")
    if verbose:
        subprocess.check_call("meshlabserver -i " + imesh_path + " -s " + script_path + " -o " + omesh_path + " "+optargs,shell=True)
    else:
        deadpipe = open(os.devnull,'w')
        subprocess.check_call("meshlabserver -i " + imesh_path + " -s " + script_path + " -o " + omesh_path + " "+optargs,shell=True,stdout=deadpipe,stderr=deadpipe)
    
def make_STL(obj, omesh_path=None):
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
            if DEBUGPRINT:
                sys.stdout.write("Creating "+omeshfolder_path+"\n")
            os.makedirs(omeshfolder_path)
        #Ideally this uses custom transformation, and isn't desctructive. But whatever.
        obj.Placement.Base.x = 0
        obj.Placement.Base.y = 0
        obj.Placement.Base.z = 0
        if DEBUGPRINT:
            sys.stdout.write("Creating "+omesh_path+"\n")
        obj.Shape.exportStl(omesh_path)
        return omesh_path
    
def make_simplified_STL(imesh_path, script_path = "./simplifymesh.mlx", omesh_path=None, n_iterations = 1):
    """
    From mesh_path, make \"simple.stl\" in the same folder using \"simplifymesh.mlx\".
    Iterates the meshlab script \"n_iterations\" times.
    """
    meshfolder_path, mesh_file = os.path.split(imesh_path)
    if not omesh_path:
        omesh_path = os.path.join(meshfolder_path, "simple.stl")
    if DEBUGPRINT:
        sys.stdout.write("Simplifying "+imesh_path+", "+str(n_iterations)+" iterations. Out: "+omesh_path+"\n")
    run_script_on_STL(imesh_path = imesh_path, script_path = script_path, omesh_path = omesh_path)
    for i in xrange(1,n_iterations):
        if DEBUGPRINT:
            sys.stdout.write(str(i))
        run_script_on_STL(imesh_path = omesh_path, script_path = script_path, omesh_path = omesh_path,verbose=False)
    if DEBUGPRINT:
        sys.stdout.write("\n")
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
    
    

if __name__=="__main__":
    #Argument handling
    import argparse
    parser = argparse.ArgumentParser(description="Convert step files into meshes.")
    parser.add_argument("cadfile",
                        help="Supported formats: .stp")
    args = parser.parse_args()
    #doc = FreeCAD.newDocument("tempdoc")
    #FreeCAD.setActiveDocument("tempdoc")
    doc = FreeCAD.newDocument("temp")
    FreeCAD.setActiveDocument("temp")
    fcimp.insert(args.cadfile,"temp")

    unique_objects = get_unique_objects(doc)
    for obj in unique_objects:
        stl_path=make_STL(obj)
        sys.stdout.write("   ")
        make_simplified_STL(stl_path,n_iterations=10)
    #print "Inserting cadfile, this may take some time."
    #fcimp.insert(args.cadfile, "tempdoc")

             
    
    
    

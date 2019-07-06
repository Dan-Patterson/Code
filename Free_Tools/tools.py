# -*- coding: utf-8 -*-
"""
=====
tools
=====

Script :  
    tools.py for npgeom

Author :  
    Dan_Patterson@carleton.ca

Modified : 
    2019-06-30

Purpose :
    Tools for working with ``free`` ArcGIS Pro functionality

Notes:

References:

    **Advanced license tools**

Some of the functions that you can replicate using this data class would
include:

`1 Feature Envelope to Polygon
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature
-envelope-to-polygon.htm>`_.

`2 Convex hulls
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/minimum
-bounding-geometry.htm>`_.

`3 Feature to Point
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature
-to-point.htm>`_.

`4 Split Line at Vertices
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/
split-line-at-vertices.htm>`_.

`5 Feature Vertices to Points
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature
-vertices-to-points.htm>`_.

`6 Polygons to Polylines
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/
feature-to-polygon.htm>`_.

`7 Frequency
<https://pro.arcgis.com/en/pro-app/tool-reference/analysis/frequency.htm>`_.


`Feature to Line
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature
-to-line.htm>`_.

`Minimum Bounding Geometry: circle, MABR, Convex Hull
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/minimum
-bounding-geometry.htm>`_.

`Polygon to Line
<https://pro.arcgis.com/en/pro-app/tool-reference/data-management/polygon
-to-line.htm>`_.

"""
# pylint: disable=C0103  # invalid-name
# pylint: disable=R0914  # Too many local variables
# pylint: disable=R1710  # inconsistent-return-statements
# pylint: disable=W0105  # string statement has no effect

import sys
#from textwrap import dedent
import importlib
import numpy as np
#from numpy.lib.recfunctions import structured_to_unstructured as stu
from numpy.lib.recfunctions import unstructured_to_structured as uts
from numpy.lib.recfunctions import append_fields

import fc_geo_io
import npGeo
from fc_geo_io import getSR, fc_data, fc_geometry, geometry_fc
from npGeo import (Geo, updateGeo, _polys_to_unique_pnts_)
#from fc_tools import *

importlib.reload(fc_geo_io)
importlib.reload(npGeo)

import arcpy
arcpy.env.overwriteOutput = True


ft = {'bool': lambda x: repr(x.astype(np.int32)),
      'float_kind': '{: 0.3f}'.format}
np.set_printoptions(edgeitems=10, linewidth=80, precision=2, suppress=True,
                    threshold=100, formatter=ft)
np.ma.masked_print_option.set_display('-')  # change to a single -

#script = sys.argv[0]  # print this should you need to locate the script

# ===========================================================================
# ---- def section: def code blocks go here ---------------------------------
msg0 = """
Either you failed to specify the geodatabase location and filename properly
or you had flotsam, including spaces, in the path, like...\n
  {}\n
Create a safe path and try again...\n
`Filenames and paths in Python`
https://community.esri.com/blogs/dan_patterson/2016/08/14/filenames-and
-file-paths-in-python.
"""

def check_path(out_fc):
    """Check for a filegeodatabase and a filename"""
    _punc_ = '!"#$%&\'()*+,-;<=>?@[]^`{|}~ '
    flotsam = " ".join([i for i in _punc_]) + " ... plus the `space`"
    msg = msg0.format(flotsam)
    if np.any([i in out_fc for i in _punc_]):
        return (None, msg)
    if "\\" in out_fc:
        pth = out_fc.split("\\")
    else:
        pth = out_fc.split("/")
    if len(pth) == 1:
        return (None, msg)
    name = pth[-1]
    gdb = "/".join(pth[:-1])
    if gdb[-4:] != '.gdb':
        return (None, msg)
    return gdb, name


def tweet(msg):
    """Print a message for both arcpy and python.
    """
    m = "\n{}\n".format(msg)
    arcpy.AddMessage(m)
    print(m)

# ---- extent_poly section --------------------------------------------------
# ---- (1)
def extent_poly(in_fc, out_fc, kind):
    """Feature envelop to polygon demo.

    Parameters
    ----------
    in_fc : string
        Full geodatabase path and featureclass filename.
    kind : integer
        2 for polygons, 1 for polylines

    References
    ----------
    `Feature Envelope to Polygon
    <https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature
    -envelope-to-polygon.htm>`_.

    >>> data = fc_data(in_fc)
    """
    result = check_path(out_fc)
    if result[0] is None:
        tweet(result[1])
        return result[1]
    gdb, name = result
    # ---- done checks       
    SR = getSR(in_fc)
    tmp, IFT, IFT_2 = fc_geometry(in_fc, SR)
    SR = getSR(in_fc)
    m = np.nanmin(tmp, axis=0)    # shift to bottom left of extent
    info = "extent to polygons"
    a = tmp - m
    g = Geo(a, IFT=IFT, Kind=kind, Info=info)   # create the geo array
    ext = g.extent_rectangles()   # create the extent array
    ext = ext + m                 # shift back, construct the output features
    ext = updateGeo(ext, K=kind, id_too=None, Info=info)
    #
    # ---- produce the geometry
    p = "POLYGON"
    if kind == 1:
        p = "POLYLINE"
    geometry_fc(ext, ext.IFT, p_type=p, gdb=gdb, fname=name, sr=SR)
    return "{} completed".format(out_fc)

# ---- convex hulls ---------------------------------------------------------
# ---- (2)
def convex_hull_polys(in_fc, out_fc, kind):
    """Determine the convex hulls on a shape basis"""
    result = check_path(out_fc)
    if result[0] is None:
        tweet(result[1])
        return result[1]
    gdb, name = result
    # ---- done checks       
    SR = getSR(in_fc)
    tmp, IFT, IFT_2 = fc_geometry(in_fc, SR)
    SR = getSR(in_fc)
    info = "convex hulls to polygons"
    g = Geo(tmp, IFT=IFT, Kind=kind, Info=info)   # create the geo array
    ch_out = g.convex_hulls(by_part=False, threshold=50)
    ch_out = updateGeo(ch_out, K=kind, id_too=None, Info=info)
    #
    # ---- produce the geometry
    p = "POLYGON"
    if kind == 1:
        p = "POLYLINE"
    geometry_fc(ch_out, ch_out.IFT, p_type=p, gdb=gdb, fname=name, sr=SR)
    return "{} completed".format(out_fc)

# ---- features to point ----------------------------------------------------
# ---- (3)
def f2pnts(in_fc):
    """Features to points"""
    result = check_path(out_fc)
    if result[0] is None:
        print(result[1])
        return result[1]
    gdb, name = result
    SR = getSR(in_fc)
    tmp, IFT, IFT_2 = fc_geometry(in_fc, SR)
    m = np.nanmin(tmp, axis=0)    # shift to bottom left of extent
    info = "feature to points"
    a = tmp - m
    g = Geo(a, IFT=IFT, Kind=kind, Info=info)   # create the geo array
    cent = g.centroids   # create the centroids
    cent = cent + m
    dt = np.dtype([('Xs', '<f8'), ('Ys', '<f8')])
    cent = uts(cent, dtype=dt)    
    return cent, SR

# ---- split line at vertices ------------------------------------------------------
# ---- (4)
def split_at_vertices(in_fc, out_fc):
    """Unique segments retained when poly geometry is split at vertices.
    
    """
    result = check_path(out_fc)
    if result[0] is None:
        print(result[1])
        return result[1]
    gdb, name = result
    SR = getSR(in_fc)
    a, IFT, IFT_2 = fc_geometry(in_fc, SR)
    ag = Geo(a, IFT)
#    fr_to = ag.unique_segments()  # geo method
    fr_to = ag.polys_to_segments()
    dt = np.dtype([('X_orig', 'f8'), ('Y_orig', 'f8'),
                   ('X_dest', 'f8'), ('Y_dest', 'f8')])
    od = uts(fr_to, dtype=dt)  # ---- unstructured to structured
    tmp = "memory/tmp"
    if arcpy.Exists(tmp):
        arcpy.Delete_management(tmp)
    arcpy.da.NumPyArrayToTable(od, tmp)
    args = [tmp, out_fc] + list(od.dtype.names) + ["GEODESIC", "", SR]
    arcpy.XYToLine_management(*args)
    return
    
# ---- vertices to points --------------------------------------------------
# ---- (5)
def p_uni_pnts(in_fc, out_fc):
    """Implements _polys_to_unique_pnts_ in npGeo methods section
    """
    result = check_path(out_fc)
    if result[0] is None:
        print(result[1])
        return result[1]
    gdb, name = result
    SR = getSR(in_fc)
    a, IFT, IFT_2 = fc_geometry(in_fc, SR)
    info = "unique points"
    g = Geo(a, IFT=IFT, Kind=kind, Info=info)   # create the geo array
    out = _polys_to_unique_pnts_(g, keep_order=True, as_structured=True)
    return out, SR

# ---- polygon to polyline --------------------------------------------------
# ---- (6)
def pgon_to_pline(in_fc, out_fc):
    """Polygon to polyline conversion"""
    result = check_path(out_fc)
    if result[0] is None:
        print(result[1])
        return result[1]
    gdb, name = result
    SR = getSR(in_fc)
    a, IFT, IFT_2 = fc_geometry(in_fc, SR)
    d = fc_data(in_fc)
    info = "pgon to pline"
    a = Geo(a, IFT=IFT, Kind=1, Info=info)   # create the geo array
    geometry_fc(a, IFT, p_type="POLYLINE", gdb=gdb, fname=name, sr=SR)
    arcpy.da.ExtendTable(out_fc, 'OBJECTID', d, 'OID_')

# ---- frequency and statistics ----------------------------------------------
# ---- (7)
def freq(a, cls_flds=None, stat_fld=None):
    """Frequency and crosstabulation

    Parameters
    ----------
    a : array
        A structured array
    flds : field
        Fields to use in the analysis

    Notes
    -----
    1. slice the input array by the classification fields
    2. sort the sliced array using the flds as sorting keys
    3. use unique on the sorted array to return the results and the counts

    >>> np.unique(ar, return_index=False, return_inverse=False,
    ...           return_counts=True, axis=None)
    """
    if stat_fld is None:
        a = a[cls_flds]  # (1) It is actually faster to slice the whole table
    else:
        all_flds = cls_flds + [stat_fld]
        a = a[all_flds]
    idx = np.argsort(a, axis=0, order=cls_flds)  # (2)
    a_sort = a[idx]
    uni, inv, cnts = np.unique(a_sort[cls_flds], False,
                               True, return_counts=True)  # (3)
    out_flds = "Counts"
    out_data = cnts
    if stat_fld is not None:
        splitter = np.where(np.diff(inv) == 1)[0] + 1
        a0 = a_sort[stat_fld]
        splits = np.split(a0, splitter)
        sums = np.asarray([np.nansum(i.tolist()) for i in splits])
        nans = np.asarray([np.sum(np.isnan(i.tolist())) for i in splits])
        mins = np.asarray([np.nanmin(i.tolist()) for i in splits])
        means = np.asarray([np.nanmean(i.tolist()) for i in splits])
        maxs = np.asarray([np.nanmax(i.tolist()) for i in splits])
        out_flds = [out_flds, stat_fld + "_sums", stat_fld + "_NaN",
                    stat_fld + "_min", stat_fld + "_mean", stat_fld + "_max"]
        out_data = [out_data, sums, nans, mins, means, maxs]
    out = append_fields(uni, names=out_flds, data=out_data, usemask=False)
    return out


# ===========================================================================
# ---- main section: testing or tool run ------------------------------------
#
script = sys.argv[0]
pth = "/".join(script.split("/")[:-1])
npGeo_tbx =  pth + "/npGeo.tbx"

frmt = """
Running... {} in in ArcGIS Pro
Using :
    input  : {}
    output : {}
    tool   : {}
    type   : {}
"""
def _testing_():
    """Run in spyder
    """
    in_fc = pth + "/npgeom.gdb/Polygons"
    out_fc = pth + "/npgeom.gdb/x1"
    tool = '9'
    kind = 0
    msg = frmt.format(script, in_fc, out_fc, tool, kind)
    result = check_path(out_fc)  # check the path
    if tool[0] not in ('1', '2', '3', '4', '5', '6', '7'):
        tweet("Tool {} not implemented".format(tool))
    if result[0] is None:
        tweet(result[1])
    else:        
        tweet(msg)
    return in_fc, out_fc, tool, kind

def _tool_():
    """run from a tool in arctoolbox in arcgis pro
    """
    in_fc = sys.argv[1]
    out_fc = sys.argv[2]
    tool = sys.argv[3]
    kind = 2
    #kind = sys.argv[4]
    msg = frmt.format(script, in_fc, out_fc, tool, kind)
    result = check_path(out_fc)  # check the path
    if result[0] is None:
        tweet(result[1])
        tweet(msg)
    else:
        gdb, name = result
        if tool[0] not in ('1', '2', '3', '4', '5', '6', '7'):
            tweet("Tool {} not implemented".format(tool))        
            kind = None        
        tweet(msg)
    return in_fc, out_fc, tool, kind
# ===========================================================================
# ---- main section: testing or tool run ------------------------------------
#
tool_list = ['1 extent polygons', '2 feature to point',
             '3 split at vertices', '4 vertices to points',
             '5 polygon to polyline', '6 frequency and statistics']

if len(sys.argv) == 1:
    testing =  True
    in_fc, out_fc, tool, kind = _testing_()
else:
    testing = False
    in_fc, out_fc, tool, kind = _tool_()

# ---- Pick the tools and process --------------------------------------------
#
t = tool[0]
#
# ---- (1) extent_poly
if t == '1':
    kind = 2
    tweet("...\nExtent polys...\n")
    result = extent_poly(in_fc, out_fc, kind)
#
# ---- (2) convex hulls
elif t == '2':
    kind = 2
    tweet("...\nConvex hulls...\n")
    result = convex_hull_polys(in_fc, out_fc, kind)
#
# ---- (3)  features to point
elif t == '3':
    tweet("...\nFeatures to Point...\n")
    cent, SR  = f2pnts(in_fc)
    if arcpy.Exists(out_fc) and arcpy.env.overwriteOutput:
        arcpy.Delete_management(out_fc)
    arcpy.da.NumPyArrayToFeatureClass(cent, out_fc, ['Xs', 'Ys'], SR)
#
# ---- (4) split at vertices
elif t == '4':
    tweet("...\nsplit at vertices...\n")
    if arcpy.Exists(out_fc) and arcpy.env.overwriteOutput:
        arcpy.Delete_management(out_fc)
    split_at_vertices(in_fc, out_fc)
#
# ---- (5) features to vertices
elif t == '5':
    out, SR = p_uni_pnts(in_fc, out_fc)
    tweet("...\nFeatures to vertices...\n")
    if arcpy.Exists(out_fc) and arcpy.env.overwriteOutput:
        arcpy.Delete_management(out_fc)
    arcpy.da.NumPyArrayToFeatureClass(out, out_fc, ['Xs', 'Ys'], SR)
#
# ---- (6) polygon to polyline
elif t == '6':
    tweet("...\nPolygons to Polylines...\n")
    if arcpy.Exists(out_fc) and arcpy.env.overwriteOutput:
        arcpy.Delete_management(out_fc)
    pgon_to_pline(in_fc, out_fc)
#
# ---- (7) frequency and statistics
elif t == '7':  
    if testing:
        cls_flds = ['Parts', 'Points']
        stat_fld = 'Shape_Area'
    else:
        cls_flds = sys.argv[3]
        stat_fld = sys.argv[4]
        cls_flds = cls_flds.split(";")  # multiple to list, singleton a list
    if stat_fld in (None, 'NoneType', ""):
        stat_fld = None
    a = arcpy.da.TableToNumPyArray(in_fc, "*")  # use the whole array
    out = freq(a, cls_flds, stat_fld)  # do freq analysis 
    if arcpy.Exists(out_fc) and arcpy.env.overwriteOutput:
        arcpy.Delete_management(out_fc)
    arcpy.da.NumPyArrayToTable(out, out_fc)
#
# ---- (
# ==== Processing finished ====
# ===========================================================================
#
if __name__ == "__main__":
    """optional location for parameters"""


from flask import Flask
import ghhops_server as hs
import numpy as np
import ee
import os
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from pyproj import Transformer

# ---------------------------------------------------------------------------------------------------------------
#                 First time use will open a webpage to authenticate the machine locally
# ---------------------------------------------------------------------------------------------------------------

# App Setup -----------------------------------------------------------------------------------------------------

# register hops app as middleware
app = Flask(__name__)
hops: hs.HopsFlask = hs.Hops(app)

# Initialize earth engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate(auth_mode='notebook')
    ee.Initialize()


# Global Functions ----------------------------------------------------------------------------------------------

def castToFloat(o):
    list = []
    for i in o:
        list.append(float(i))

    return list

def pts_bbox(pts):
    pts_py = []
    for p in pts:
        pts_py.append([p.X, p.Y])

    aoi = ee.Geometry.Polygon(
        [[[pts_py[0][0], pts_py[0][1]],
        [pts_py[1][0], pts_py[1][1]],
        [pts_py[2][0], pts_py[2][1]],
        [pts_py[3][0], pts_py[3][1]]]], None, False)

    return aoi;

def pts_polygon(pts):

    coords = []
    for p in pts:

        coord = [p.X,p.Y]
        coords.append(coord)

    geom_polygon = ee.Geometry.Polygon([ee.Geometry.LinearRing(coords)])

    return geom_polygon

def pts_multipts(pts):

    coords = []
    for p in pts:

        coord = [p.X,p.Y]
        coords.append(coord)

    geom_pts = ee.Geometry.MultiPoint(coords)

    return geom_pts

def img_scaleTrim(image, band, mode, proj, scale, pts):

    # Create reducer for sampling mode
    reducer = "ee.Reducer."+ mode +"()"

    # Resample the image to assign custom scale
    imageResampled = image \
        .reduceResolution(reducer= eval(reducer), maxPixels = 5000) \
        .reproject(crs='EPSG:4326', scale=scale)

    # Extract the bounding region from the locations
    aoi = pts_bbox(pts)

    # Sample the image within the region
    rec_sample = imageResampled.sampleRectangle(region=aoi, defaultValue=0)

    # Prepare the outputs
    np_values = np.array(rec_sample.get(band).getInfo())
    values = np_values.flatten().tolist()

    # Change from pixel to node (vertices)
    H = np_values.shape[0] -1
    W = np_values.shape[1] -1

    return values,W,H;

# App Components -----------------------------------------------------------------------------------------------

@hops.component(
    "/ee_image",
    inputs=[
        hs.HopsString("layer", "layer"),
        hs.HopsString("bands", "bands"),
        hs.HopsString("mode","mode", "resampling mode to be applied. Default is mean", default="mean"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("pts","pts","the bounding box representing the area of analaysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_image(layer,bands,mode,scale,pts):

    # Select image layer
    image = ee.Image(layer)\
        .select(bands)

    # Extract original projection
    proj = image.projection()

    return img_scaleTrim(image, bands, mode, proj, scale, pts);


@hops.component(
    "/ee_filterDate",
    inputs=[
        hs.HopsString("layer", "layer"),
        hs.HopsString("dates", "dates", "first and last day to download", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsString("layers"),
        hs.HopsString("days")
    ],
)

def ee_filterDate(layer,dates):

    # Filter image collection
    images = ee.ImageCollection(layer) \
             .filter(ee.Filter.date(dates[0],dates[1]))

    # Get metadata
    meta = images.getInfo()
    length = len(meta["features"])
    layers = []
    days = []

    for i in range(length):
        layer = meta["features"][i]["id"]
        day = meta["features"][i]["properties"]["system:index"]
        layers.append(layer)
        days.append(day)

    return (layers, days);


@hops.component(
    "/ee_nd",
    inputs=[       
        hs.HopsString("layer", "layer"),
        hs.HopsString("band1", "band1"),        
        hs.HopsString("band2", "band2"),
        hs.HopsString("mode","mode", "resampling mode to be applied. Default is mean", default="mean"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("pts","pts","the region to sample. can be bounding box or polygon depending on bbox boolean", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_ND(layer,band1,band2,mode,scale,pts):

    # Select the two bands to subtract
    image1 = ee.Image(layer).select(band1)
    image2 = ee.Image(layer).select(band2)

    # Compute Normalized Difference
    imageND = image1.subtract(image2) \
              .divide(image1.add(image2)) \
              .rename("ND")

    # Extract original projection
    proj = image1.projection()

    return img_scaleTrim(imageND, "ND", mode, proj, scale, pts)

@hops.component(
    "/ee_cumCost",
    inputs=[
        hs.HopsString("layer", "layer", "the layer from which to calculate the cost to traverse"),
        hs.HopsString("cost", "cost", "the cost band"),
        hs.HopsPoint("sources", "sources", "the location to where to calculate the proximity", hs.HopsParamAccess.LIST),
        hs.HopsNumber("maxdistance", "maxd"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("pts","bbox","the bounding box representing the area of analaysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_cumCost(layer,cost,sources,maxd,scale,pts):

    # Compute the centroid location
    geom_source = pts_multipts(sources)

    # Rasterize location into an image where the geometry is 1, everything else is 0
    imageSources = ee.Image().toByte().paint(geom_source, 1)

    # Mask the sources image with itself.
    imageSources = imageSources.updateMask(imageSources)

    # Select cost data
    cost = ee.Image(layer)\
        .select(cost)

    # Extract original projection
    proj = cost.projection()

    # Resample resolution
    costResample = cost \
        .reduceResolution(**{
        'reducer': ee.Reducer.mean(),
        'maxPixels': 5000
        }) \
        .reproject(**{
        'crs': proj,
        'scale': scale
        })

    # Compute the cumulative cost
    cumulativeCost = costResample.cumulativeCost(source=imageSources, maxDistance=ee.Number.float(maxd)) \
        .rename("cumcost")

    return img_scaleTrim(ee.Image(cumulativeCost), "cumcost", "mean", proj, scale, pts)

@hops.component(
    "/ee_cumCostExtra",
    inputs=[
        hs.HopsString("layer", "layer", "the layer from which to calculate the cost to traverse"),
        hs.HopsString("cost", "cost", "the cost band"),
        hs.HopsString("remap", "remap", "pairs of x=y values to remap the image into minute/meter cost values", hs.HopsParamAccess.LIST),
        hs.HopsNumber("default","default","default"),
        hs.HopsPoint("pts", "paint", "points to paint on top of cost map", hs.HopsParamAccess.LIST),
        hs.HopsNumber("val","val","cost applied to the paint in minute/meter"),
        hs.HopsPoint("sources", "sources", "the location to where to calculate the proximity", hs.HopsParamAccess.LIST),
        hs.HopsNumber("maxdistance", "maxd"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("bounding box","bbox","the bounding box representing the area of analaysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_cumCostExtra(layer,cost,remap,default,paint,val,sources,maxd,scale,pts):

    # Compute the centroid location
    geom_source = pts_multipts(sources)

    # Rasterize location into an image where the geometry is 1, everything else is 0
    imageSources = ee.Image().toByte().paint(geom_source, 1)

    # Mask the sources image with itself.
    imageSources = imageSources.updateMask(imageSources)
    
    # Prepare values for remapping
    fromVals = []
    toVals = []

    for m in remap:
        fromVals.append(m.split("=")[0])
        toVals.append(m.split("=")[1])

    # Convert int values
    fromVals = castToFloat(fromVals)
    toVals = castToFloat(toVals)

     # Create the cost layer
    cost = ee.Image(layer).select(cost) \
        .remap(fromVals, toVals, defaultValue=default)

    # Extract original projection
    proj = cost.projection()

    # Resample resolution
    costResample = cost \
        .reduceResolution(**{
        'reducer': ee.Reducer.mean(),
        'maxPixels': 5000
        }) \
        .reproject(**{
        'crs': proj,
        'scale': scale
        })

    # Paint cost
    geom_pts = pts_multipts(paint)

    costResampledPaint = costResample.paint(geom_pts, val).rename("cumcost")

    # Compute the cumulative cost
    cumulativeCost = costResampledPaint.cumulativeCost(source=imageSources, maxDistance=ee.Number.float(maxd)) \
        .rename("cumcost")

    return img_scaleTrim(ee.Image(cumulativeCost), "cumcost", "mean", proj, scale, pts)



@hops.component(
    "/reproject_UTM",
    name="reproject based on bounding box",
    description="reproject locations from 4326 to local UTM",

    inputs=[
        hs.HopsPoint("points","pts","the projected points", hs.HopsParamAccess.LIST),
        hs.HopsBoolean("bool","xyz?","should the boundingbox be moved to the origin?", default=False)
    ],
    outputs=[
        hs.HopsString("points","p","the projected points")
    ]
)


def reproject_UTM(pts, bool):

    # Compute the centroid location
    xs = []
    ys = []

    for p in pts:
        xs.append(p.X)
        ys.append(p.Y)

    p_mean = [np.asarray(xs).mean(),np.asarray(ys).mean()]

    # Extract UTM of the centroid location
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            south_lat_degree=p_mean[1],
            west_lon_degree=p_mean[0],
            north_lat_degree=p_mean[1],
            east_lon_degree=p_mean[0]
        ),
    )

    # Project from 4326 to local UTM
    WSG84_crs = CRS.from_epsg(4326)
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    transformer = Transformer.from_crs(WSG84_crs, utm_crs, always_xy=True)

    pts_UTM = []

    p_leftbottom = transformer.transform(pts[0].X,pts[0].Y)

    for p in pts:

        # provide first X then Y -- Lon then Lat
        p_UTM = transformer.transform(p.X,p.Y)

        # Move to origin using left bottom corner
        if bool == True:
            p_UTM = [p_UTM[0] - p_leftbottom[0], p_UTM[1] - p_leftbottom[1]]

        pts_UTM.append(str("{" + str(p_UTM[0]) +"," + str(p_UTM[1]) + ",0}"))

    return pts_UTM;


# Run App ------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask
import ghhops_server as hs
import rhino3dm
import pandas as pd
import numpy as np
import ee
import geemap
import os
from pyproj import CRS
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from pyproj import Transformer

# Make to first run hello_ee.py to do the one-time authentication to Earth Engine

# register hops app as middleware
app = Flask(__name__)
hops: hs.HopsFlask = hs.Hops(app)


# Initial earth engine
ee.Initialize()

@hops.component(
    "/ee_image",
    inputs=[       
        hs.HopsString("layer", "layer"),
        hs.HopsString("bands", "bands"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("bounding box","bbox","the bounding box representing the area of analysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_image(layer,bands,scale,pts):

    print(type(layer))
    print(bands)
    # Create a map to upload the layers to.
    Map = geemap.Map()

    # Add image layer
    image = ee.Image(layer)\
        .select(bands) 

    layer_viz = {
        'bands': [bands]
    }
    Map.addLayer(image, layer_viz, None, False, 1)

    imageProjection = image.projection()

    # Resample the image to assign custom scale
    imageResampled = image \
        .reduceResolution(**{
        'reducer': ee.Reducer.mean(),
        'maxPixels': 5000
        }) \
        .reproject(**{
        'crs': imageProjection,
        'scale': scale
        })

    pts_py = []
    print(pts)
    for p in pts: 
        pts_py.append([p.X, p.Y])

    aoi = ee.Geometry.Polygon(
        [[[pts_py[0][0], pts_py[0][1]],
        [pts_py[1][0], pts_py[1][1]],
        [pts_py[2][0], pts_py[2][1]],
        [pts_py[3][0], pts_py[3][1]]]], None, False)

    # rgb is a three dimension array (firt two being the data and third being relative to the band)
    rgb_img = geemap.ee_to_numpy(imageResampled, default_value=0, region=aoi)
    H = rgb_img.shape[0]
    W = rgb_img.shape[1]
    
    return rgb_img.flatten().tolist(),W,H,;

@hops.component(
    "/ee_imageCollection",
    inputs=[       
        hs.HopsString("layer", "layer"),
        hs.HopsString("date", "date", "input date", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsString("layer")
    ],
)


def ee_imageCollection(layer,date):    

    # Create a map to upload the layers to.
    Map = geemap.Map()

    # Add image layer and filter on Dates
    imageCollection = ee.ImageCollection(layer)\
                    .filterDate(date[0],date[1])

    image = ee.Image(imageCollection.first())

    return image.getInfo().get("id");



@hops.component(
    "/ee_nd",
    inputs=[       
        hs.HopsString("layer", "layer"),
        hs.HopsString("band1", "band1"),        
        hs.HopsString("band2", "band2"),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("bounding box","bbox","the bounding box representing the area of analaysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ],
)

def ee_ND(layer,band1,band2,scale,pts):

    Map = geemap.Map()
    # Add Earth Engine dataset
    landsat = ee.Image(layer)

    # Compute NDVI the easy way.
    ndvi1999 = landsat.normalizedDifference([band1, band2])

    # Add image layer
    image = ndvi1999 

    Map.addLayer(image, {}, None, False, 1)
    imageProjection = image.projection()

    # Resample the image to assign custom scale
    imageResampled = image \
        .reduceResolution(**{
        'reducer': ee.Reducer.mode(),
        'maxPixels': 5000
        }) \
        .reproject(**{
        'crs': imageProjection,
        'scale': scale
        })

    pts_py = []
    print(pts)
    for p in pts: 
        pts_py.append([p.X, p.Y])

    aoi = ee.Geometry.Polygon(
        [[[pts_py[0][0], pts_py[0][1]],
        [pts_py[1][0], pts_py[1][1]],
        [pts_py[2][0], pts_py[2][1]],
        [pts_py[3][0], pts_py[3][1]]]], None, False)

    # rgb is a three dimension array (firt two being the data and third being relative to the band)
    rgb_img = geemap.ee_to_numpy(imageResampled, default_value=0, region=aoi)
    H = rgb_img.shape[0]
    W = rgb_img.shape[1]
    
    return rgb_img.flatten().tolist(),W,H,;


@hops.component(
    "/reproject_UTM",
    name="reproject based on bounding box",
    description="reproject locations from 4326 to local UTM",
    
    inputs=[
        hs.HopsPoint("points","pts","the projected points", hs.HopsParamAccess.LIST)
    ],
    outputs=[
        hs.HopsPoint("points","p","the projected points")
    ]
)

def reproject_UTM(pts):

    
    # Extract the average location
    xs = []
    ys = []

    for p in pts: 
        xs.append(p.X)
        ys.append(p.Y)

    p_mean = [np.asarray(xs).mean(),np.asarray(ys).mean()]
    
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
    
    for p in pts:

        # provide first X then Y -- Lon then Lat
        p_UTM = transformer.transform(p.X,p.Y)
        pts_UTM.append(rhino3dm.Point3d(p_UTM[0], p_UTM[1], 0))

    return pts_UTM;

# Run app
if __name__ == "__main__":
    app.run(debug=True)

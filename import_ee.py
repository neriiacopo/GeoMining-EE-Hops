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
    ee.Authenticate()
    ee.Initialize()

# Global Functions ----------------------------------------------------------------------------------------------

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

def img_scaleTrim(image, band, proj, scale, pts):
    
    # Resample the image to assign custom scale
    imageResampled = image \
        .reduceResolution(**{
        'reducer': ee.Reducer.mean(),
        'maxPixels': 5000
        }) \
        .reproject(**{
        'crs': proj,
        'scale': scale
        })

    # Extract the bounding region from the locations
    aoi = pts_bbox(pts)

    # Sample the image within the region
    rec_sample = imageResampled.sampleRectangle(region=aoi, defaultValue=0)

    # Prepare the outputs
    rgb_img = np.array(rec_sample.get(band).getInfo())

    # Change from pixel to node (vertices)
    H = rgb_img.shape[0] -1
    W = rgb_img.shape[1] -1
    
    return rgb_img.flatten().tolist(),W,H,;


# App Components -----------------------------------------------------------------------------------------------

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

    # Select image layer
    image = ee.Image(layer)\
        .select(bands) 

    # Extract original projection
    proj = image.projection()

    return img_scaleTrim(image, bands, proj, scale, pts);


@hops.component(
    "/ee_imageCollection",
    inputs=[       
        hs.HopsString("layer", "layer"),
        hs.HopsString("bands", "bands"),
        hs.HopsString("date", "date", "input date", hs.HopsParamAccess.LIST),
        hs.HopsNumber("scale", "scale"),
        hs.HopsPoint("bounding box","bbox","the bounding box representing the area of analysis. Note, provide it in the following order: min.Lon(X), max.Lon(X), min.Lat(Y), max.Lat(Y) aka LeftBottom, RightBottom, RightTop, LeftTop", hs.HopsParamAccess.LIST)],
    outputs=[
        hs.HopsNumber("values"),
        hs.HopsNumber("W"),
        hs.HopsNumber("H")
    ]
)

def ee_imageCollection(layer,bands,date,scale,pts):    

    # Extract the bounding region from the locations
    aoi = pts_bbox(pts)

    # Select image layer and filter on Region and Dates
    imageCollection = ee.ImageCollection(layer)\
                    .select(bands)\
                    .filterBounds(aoi)\
                    .filterDate(date[0],date[1])\
                    .limit(10)

    # Extract original projection
    proj = imageCollection.first().projection()

    # Create a mosaic from available collection
    imageMosaic = ee.Image(imageCollection.mosaic())\
                            .setDefaultProjection(imageProjection)

    return img_scaleTrim(imageMosaic, bands, proj, scale, pts);

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

    # Select the two bands to subtract
    image1 = ee.Image(layer).select(band1)
    image2 = ee.Image(layer).select(band2)

    # Compute Normalized Difference
    imageND = image1.subtract(image2) \
              .divide(image1.add(image2)) \
              .rename("ND")

    # Extract original projection
    proj = image1.projection()

    return img_scaleTrim(imageND, "ND", proj, scale, pts)
    
@hops.component(
    "/ee_cumCost",
    inputs=[       
        hs.HopsString("layer", "layer", "the layer from which to calculate the cost to traverse"),
        hs.HopsString("cost", "cost"),        
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

def ee_cumCost(layer,cost,sources,maxd,scale,pts):

    # Compute the centroid location
    coords = []
    for p in sources: 

        coord = [p.X,p.Y]
        coords.append(coord)

    geom_source = ee.Geometry.MultiPoint(coords)

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

    return img_scaleTrim(ee.Image(cumulativeCost), "cumcost", proj, scale, pts)

@hops.component(
    "/reproject_UTM",
    name="reproject based on bounding box",
    description="reproject locations from 4326 to local UTM",
    
    inputs=[
        hs.HopsPoint("points","pts","the projected points", hs.HopsParamAccess.LIST)
    ],
    outputs=[
        hs.HopsString("points","p","the projected points")
    ]
)

def reproject_UTM(pts):

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
    
    for p in pts:

        # provide first X then Y -- Lon then Lat
        p_UTM = transformer.transform(p.X,p.Y)
        pts_UTM.append(str("{" + str(p_UTM[0]) +"," + str(p_UTM[1]) + ",0}"))

    return pts_UTM;


# Run App ------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)

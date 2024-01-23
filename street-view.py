# Run this with the arcgis python
from arcgis.gis import GIS
from arcgis.gis import Layer
from arcgis.geometry import Polyline
from arcgis.geometry import Point
from arcgis.geometry import project
from PIL import Image
from pathlib import Path
import urllib.request
import csv
import os

# Globals
# For ArcGIS online
gis = GIS(username=input("Enter agol user: "), password=input("Enter agol password: "))
print("Connected...")

# Item ID for Testing Layer
roadItemID = 'ENTER ITEM ID'

# For Google URL
fov = 120
api_key = 'PASTE YORU GOOGLE API KEY'

# Import feature-service (aka feature layer) using ArcGIS API gis.content.get('itemIdString')
undriven_roads = gis.content.get(roadItemID)

# Below this line is the feature layer
undriven_road_features = undriven_roads.layers[0]
undriven_road_feature_set = undriven_road_features.query()
all_features = undriven_road_feature_set.features
#print(type(undriven_roads))
#print(type(undriven_road_features))
#print(undriven_road_feature_set)

in_CS = 3857
out_CS = 4326

# Functions
def delete_attachment(oid, lyr,):
    pass

def make_dir(oid):
    pth = f'./g_photo/{oid}'
    Path(pth).mkdir(parents=True, exist_ok=True)
    return pth

def make_url(lat, lon, heading):
    url = f"https://maps.googleapis.com/maps/api/streetview?size=1200x1200&location={lat},{lon}&fov={fov}&heading={heading}&pitch=0&key={api_key}"
    return url

def crop_image(imagen):
    img = Image.open(imagen)
    img_crop = img.crop((0, 0, 640, 615))
    img_crop.save(imagen, quality=100)

def download_img(lat,lon,path, oid):
    # Image name must include path to local disk
    # Start making a list of all of the files you are downloading (path included)
    # Download images into folder
    for photoHeading in range(0,360,90):
        url_string = make_url(lat,lon,photoHeading)
        img_name = path + f"/{oid}_heading{photoHeading}.jpg"
        urllib.request.urlretrieve(url_string, img_name)
        #Crops bottom 25 pixels from image
        crop_image(img_name)

# Makes a URL of for Street View Purposes
def street_view_url(lat,lon):
    baseURL = f"https://www.google.com/maps/@{lat},{lon},18z"
    return baseURL

def add_attachment(oid, lyr, img_path):
    """Use the add() method on attachments property of a FeatureLayer object to add new attachments
    to a feature.It accepts the object id of the feature and path to attachment as parameters"""
    img_list = os.listdir(img_path)
    # Loop through files in folder and attach
    for i in img_list:
        if i.endswith('.jpg'):
            lyr.attachments.add(oid, i)
            print(f"Added {i} to feature with ObjectID:{oid}")
    return

def main():
    # Use this loop to run through all the functions(ie. make URL, populate fields, download google images, add attachments
    for line in undriven_road_feature_set:
        # the object id in question
        line_oid = line.attributes['OBJECTID']

        # Create geometry object from feature coordinates. Need it for geometry object's centroid function
        polyline = Polyline(line.geometry)
        center_string = str(polyline.centroid)
        x_webmerc = float(center_string.split(',')[0][1:])
        y_webmerc = float(center_string.split(',')[1][:-1])
        centroid_pt = Point({"x":x_webmerc, "y":y_webmerc, "spatialReference":{"wkid" : 3857} })

        # Reprojected Centroid point to get the Latitude and Longitude (not northing, easting)
        centroid_reproj = project(geometries=[centroid_pt], in_sr=in_CS, out_sr=out_CS)
        print(f"ObjectID: {line.attributes['OBJECTID']}\tCentroid: {centroid_reproj}")

        # Make folder for images
        current_img_path = make_dir(line_oid)

        try:
            # Download Images
            download_img(centroid_reproj[0]['y'], centroid_reproj[0]['x'], current_img_path, line_oid)
        except:
            print(f"No streetview available for feature with ObjectID: {line_oid}")
            continue

        # Add images as attachments
        img_list = os.listdir(current_img_path)
        # Loop through files in folder and attach
        for i in img_list:
            if i.endswith('.jpg'):
                undriven_road_features.attachments.add(line_oid, f"{current_img_path}/{i}")
                print(f"Added {i} to feature with ObjectID:{line_oid}")
        #add_attachment(line_oid, all_features, current_img_path)
    

if __name__ == "__main__":
    main()







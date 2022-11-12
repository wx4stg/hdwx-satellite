#!/usr/bin/env python3
# Geocolor satellite product generation for python HDWX
# Created 27 October 2022 by Sam Gardner <stgardner4@tamu.edu>


import xarray as xr
from matplotlib import pyplot as plt
import numpy as np
from cartopy import crs as ccrs
from cartopy import feature as cfeat
import metpy
from os import path, system, remove
import pandas as pd
from siphon.catalog import TDSCatalog
from os import path
from pathlib import Path
from datetime import datetime as dt, timedelta
import json
import atexit
from time import sleep

@atexit.register
def exitFunc():
    print("sleeping")
    sleep(15)
    remove("geocolor-lock.txt")
    system("bash generate.sh &")

basePath = path.dirname(path.abspath(__file__))
if path.exists(path.join(basePath, "HDWX_helpers.py")):
    import HDWX_helpers
    hasHelpers = True
else:
    hasHelpers = False

def plotSat():
    # Get the satellite data
    dataAvail = TDSCatalog("https://thredds.ucar.edu/thredds/catalog/satellite/goes/east/products/GeoColor/CONUS/Channel01/current/catalog.xml").datasets[-1]
    dataAvail2 = TDSCatalog("https://thredds.ucar.edu/thredds/catalog/satellite/goes/east/products/GeoColor/CONUS/Channel02/current/catalog.xml").datasets[-1]
    dataAvail3 = TDSCatalog("https://thredds.ucar.edu/thredds/catalog/satellite/goes/east/products/GeoColor/CONUS/Channel03/current/catalog.xml").datasets[-1]
    if dataAvail.name.split("_")[3] != dataAvail2.name.split("_")[3] or dataAvail.name.split("_")[3] != dataAvail3.name.split("_")[3]:
        print("De-sync detected, waiting")
        exit()
    latestTimeAvailable = dt.strptime(dataAvail.name.split("_")[3], "s%Y%j%H%M170")
    outputMetadataPath = path.join(basePath, "output", "metadata", "products", "5", latestTimeAvailable.strftime("%Y%m%d%H00") + ".json")
    if path.exists(outputMetadataPath):
        with open(outputMetadataPath, "r") as f:
            currentRunMetadata = json.load(f)
        lastPlottedTime = dt.strptime(currentRunMetadata["productFrames"][-1]["valid"], "%Y%m%d%H%M")
        if lastPlottedTime >= latestTimeAvailable:
            print("Nothing to do")
            exit()
    channel01 = dataAvail.remote_access(use_xarray=True)
    channel02 = dataAvail2.remote_access(use_xarray=True)
    channel03 = dataAvail3.remote_access(use_xarray=True)
    print("Download complete!")
    blue = channel01.Sectorized_CMI.data
    red = channel02.Sectorized_CMI.data
    green = channel03.Sectorized_CMI.data
    pngdata = np.dstack([red/np.max(red), green/np.max(green), blue/np.max(blue)])
    
    
    cfmetadata = channel01.metpy.parse_cf("Sectorized_CMI")
    satProj = cfmetadata.metpy.cartopy_crs
    img_extent = [cfmetadata.x.min(), cfmetadata.x.max(), cfmetadata.y.min(), cfmetadata.y.max()]
    validTime = pd.to_datetime(cfmetadata.time.data)

    fig = plt.figure()
    ax = plt.axes(projection=satProj)
    ax.imshow(pngdata, transform=satProj, interpolation="none", extent=img_extent)
    ax.add_feature(cfeat.COASTLINE.with_scale("50m"), linewidth=1, edgecolor="black", zorder=10)
    ax.add_feature(cfeat.STATES.with_scale("50m"), linewidth=0.5, edgecolor="black")
    outputPath = path.join(basePath, "output", "products", "satellite", "goes16", "geocolor", validTime.strftime("%Y"), validTime.strftime("%m"), validTime.strftime("%d"), validTime.strftime("%H00"), validTime.strftime("%M.png"))
    Path(path.dirname(outputPath)).mkdir(parents=True, exist_ok=True)
    if hasHelpers:
        HDWX_helpers.dressImage(fig, ax, "GOES-16 CONUS GeoColor", validTime, notice="GeoColor developed by NOAA/CIRA", width=3840, height=2160)
    fig.savefig(outputPath)
    if hasHelpers:
        HDWX_helpers.writeJson(path.abspath(path.dirname(__file__)), 5, runTime=(validTime - timedelta(minutes=validTime.minute)), fileName=validTime.strftime("%M.png"), validTime=validTime, gisInfo=["0,0", "0,0"], reloadInterval=60)
    plt.close(fig)
    print("Done!")


if __name__ == "__main__":
    plotSat()

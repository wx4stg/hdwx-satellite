#!/usr/bin/env python3
# Geocolor satellite product generation for python HDWX
# Created 27 October 2022 by Sam Gardner <stgardner4@tamu.edu>


import xarray as xr
from matplotlib import pyplot as plt
import numpy as np
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from os import path, remove
from siphon.catalog import TDSCatalog
from os import path
from pathlib import Path
from datetime import datetime as dt, timedelta
import json
import sys
from pyxlma import coords
from timeoutcontext import timeout

axExtent = [-125, -65, 24, 50]
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
        exit()
    latestTimeAvailable = dt.strptime(dataAvail.name.split("_")[3][:-3], "s%Y%j%H%M")
    outputMetadataPath = path.join(basePath, "output", "metadata", "products", "5", latestTimeAvailable.strftime("%Y%m%d%H00") + ".json")
    if path.exists(outputMetadataPath):
        with open(outputMetadataPath, "r") as f:
            currentRunMetadata = json.load(f)
        lastPlottedTime = dt.strptime(currentRunMetadata["productFrames"][-1]["valid"], "%Y%m%d%H%M")
        if lastPlottedTime >= latestTimeAvailable:
            exit()
    with timeout(30):
        channel01 = dataAvail.download(filename='./ch01.nc')
        channel01 = xr.open_dataset('ch01.nc', chunks='auto')
        channel02 = dataAvail2.download(filename='./ch02.nc')
        channel02 = xr.open_dataset('ch02.nc', chunks='auto')
        channel03 = dataAvail3.download(filename='./ch03.nc')
        channel03 = xr.open_dataset('ch03.nc', chunks='auto')
    
    blue = channel01.Sectorized_CMI.data
    red = channel02.Sectorized_CMI.data
    green = channel03.Sectorized_CMI.data
    pngdata = np.dstack([red/np.max(red), green/np.max(green), blue/np.max(blue)])
    
    satsys = coords.GeostationaryFixedGridSystem(subsat_lon=channel01.satellite_longitude, sweep_axis='x')
    geosys = coords.GeographicSystem()
    x2d, y2d = np.meshgrid(channel01.x/1e6, channel01.y/1e6)
    lon, lat, alt = geosys.fromECEF(*satsys.toECEF(x2d, y2d, np.zeros_like(x2d)))
    lon.shape = x2d.shape
    lat.shape = x2d.shape

    for i in range(3):
        pngdata[:, :, i] = np.where(np.abs(lon) == np.inf, np.nan, pngdata[:, :, i])
        pngdata[:, :, i] = np.where(np.abs(lat) == np.inf, np.nan, pngdata[:, :, i])
    lon[np.abs(lon) == np.inf] = np.nanmin(lon)
    lat[np.abs(lat) == np.inf] = -99
    lat[np.abs(lat) == -99] = np.nanmax(lat)
    
    lon = coords.centers_to_edges_2d(lon)
    lat = coords.centers_to_edges_2d(lat)

    validTime = dt.strptime(channel01.start_date_time, '%Y%j%H%M%S')

    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.pcolorfast(lon, lat, pngdata, transform=ccrs.PlateCarree())
    ax.add_feature(cfeat.COASTLINE.with_scale("50m"), linewidth=1, edgecolor="black", zorder=10)
    ax.add_feature(cfeat.STATES.with_scale("50m"), linewidth=0.5, edgecolor="black")
    px = 1/plt.rcParams["figure.dpi"]
    fig.set_size_inches(3840*px, 2160*px)
    ax.set_extent(axExtent, crs=ccrs.PlateCarree())

    outputPath = path.join(basePath, "output", "products", "satellite", "goes16", "geocolor", validTime.strftime("%Y"), validTime.strftime("%m"), validTime.strftime("%d"), validTime.strftime("%H00"), validTime.strftime("%M.png"))
    Path(path.dirname(outputPath)).mkdir(parents=True, exist_ok=True)
    if hasHelpers:
        HDWX_helpers.dressImage(fig, ax, "GOES-16 CONUS GeoColor", validTime, notice="GeoColor developed by NOAA/CIRA", width=3840, height=2160)
    if hasHelpers:
        HDWX_helpers.saveImage(fig, outputPath)
        HDWX_helpers.writeJson(path.abspath(path.dirname(__file__)), 5, runTime=(validTime - timedelta(minutes=validTime.minute)), fileName=validTime.strftime("%M.png"), validTime=validTime, gisInfo=["0,0", "0,0"], reloadInterval=270)
    else:
        fig.savefig(outputPath)
    plt.close(fig)

    if "--no-gis" not in sys.argv:
        gisFig = plt.figure()
        gisAx = plt.axes(projection=ccrs.PlateCarree())
        gisAx.set_extent(axExtent, crs=ccrs.PlateCarree())
        gisAx.pcolorfast(lon, lat, pngdata, transform=ccrs.PlateCarree())
        gisOutputPath = path.join(basePath, "output", "gisproducts", "satellite", "goes16", "geocolor", validTime.strftime("%Y"), validTime.strftime("%m"), validTime.strftime("%d"), validTime.strftime("%H00"), validTime.strftime("%M.png"))


        Path(path.dirname(gisOutputPath)).mkdir(parents=True, exist_ok=True)
        gisAx.set_position([0, 0, 1, 1])
        gisFig.set_size_inches(3840*px, 2160*px)
        extent = gisAx.get_tightbbox(gisFig.canvas.get_renderer()).transformed(gisFig.dpi_scale_trans.inverted())
        gisFig.savefig(gisOutputPath, transparent=True, bbox_inches=extent)
        if hasHelpers:
            HDWX_helpers.writeJson(path.abspath(path.dirname(__file__)), 4, runTime=(validTime - timedelta(minutes=validTime.minute)), fileName=validTime.strftime("%M.png"), validTime=validTime, gisInfo=["0,0", "0,0"], reloadInterval=270)

    for i in range(1, 4):
        remove(f'ch0{i}.nc')

if __name__ == "__main__":
    plotSat()

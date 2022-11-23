#!/bin/bash
# Product generation script for hdwx-satellite
# Created 28 October 2022 by Sam Gardner <stgardner4@tamu.edu>

if [ -f ../config.txt ]
then
    source ../config.txt
else
    condaEnvName="HDWX"
fi
if [ -f ../HDWX_helpers.py ]
then
    if [ -f ./HDWX_helpers.py ]
    then
        rm ./HDWX_helpers.py
    fi
    cp ../HDWX_helpers.py ./
fi
if [ ! -d output/ ]
then
    mkdir output/
fi

if [ -f geocolor-lock.txt ]
then
    pidToCheck=`cat geocolor-lock.txt`
    if ! kill -0 $pidToCheck
    then
        $condaRootPath/envs/$condaEnvName/bin/python3 geocolor.py &
        echo -n $! > geocolor-lock.txt
    else
        echo "GeoColor locked"
    fi
else
    $condaRootPath/envs/$condaEnvName/bin/python3 geocolor.py &
    echo -n $! > geocolor-lock.txt
fi
if [ "$1" != "--no-cleanup" ]
then
    echo "Cleaning..."
    $condaRootPath/envs/$condaEnvName/bin/python3 cleanup.py
fi

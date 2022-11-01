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

$condaRootPath/envs/$condaEnvName/bin/python3 geocolor.py
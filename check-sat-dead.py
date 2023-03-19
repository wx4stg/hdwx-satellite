#!/usr/bin/env python3
# Check to see if satellite plotter is stuck downloading
# Created 19 March 2023 by Sam Gardner <stgardner4@tamu.edu>

import json
from os import path, system, remove
from datetime import datetime as dt

if __name__ == "__main__":
    basePath = path.dirname(path.abspath(__file__))
    productJsonPath = path.join(basePath, "output", "metadata", "5.json")
    if path.exists(productJsonPath):
        with open(productJsonPath, "r") as f:
            productJson = json.load(f)
        lastRunTime = dt.strptime(productJson["lastReloadTime"], "%Y%m%d%H%M")
        if (dt.utcnow() - lastRunTime).total_seconds() > 600:
            pidFile = path.join(basePath, "geocolor-lock.txt")
            if path.exists(pidFile):
                with open(pidFile, "r") as f:
                    pid = f.read()
                system("kill -9 " + pid)
                remove(pidFile)
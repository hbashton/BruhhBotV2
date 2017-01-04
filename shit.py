#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from json import JSONDecoder
import os

def loadjson(PATH, filename):
    if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
        print ("Either file is missing or is not readable. Creating.")
        name = {}
        with open(filename, 'w') as f:
            json.dump(name, f)
    with open(filename) as f:
        name = json.load(f)
    return name

def dumpjson(filename, var):
    with open(filename, 'w') as f:
        json.dump(var, f)


idbase = loadjson('./idbase.json', "idbase.json")
newidbase = loadjson('./newidbase.json', "newidbase.json")
for key in idbase.keys():
    for userid, username in idbase[key].items():
        if userid not in newidbase.keys():
            newidbase[userid] = username
dumpjson("newidbase.json", newidbase)

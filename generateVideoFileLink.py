#!/usr/bin/env python
"""
This python Generate XML file from Mythtv jobqueue 

Copyright 2016 Markus Kastner

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import xml.etree.ElementTree as ET
import os
import sys
import argparse
from MythTV import MythDB, findfile, Recorded
from  MythTV.dataheap import Recorded
#from  MythTV.system import System
#from  MythTV.logging import MythLog
from  MythTV.mythproto import findfile
# Taken from https://github.com/wagnerrp/mythtv-scripts/blob/master/python/mythlink.py
def gen_link(rec, dest):
    sg = findfile(rec.basename, rec.storagegroup, rec._db)
    source = os.path.join(sg.dirname, rec.basename)
    destination = os.path.join(dest, rec.basename)
    destination = destination.replace(' ','_')
    print(source, destination)
    try:
        os.symlink(source, destination)
    except OSError:
        pass
    return destination

if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Generate XML file from Mythtv jobqueue.')
    parser.add_argument('findid', help='FINDID parameter from Mythtv Backend')
#    parser.add_argument('chanid', help='Mythtv channel id of a recording')
#    parser.add_argument('recordedid', help='xxxMythtv start time (UTC) of a recording')
#    parser.add_argument('starttime', help='Mythtv start time (UTC) of a recording')
    parser.add_argument("-o",'--destination', help='Destination path (/data_2/transcode/output if not set)')
    args = parser.parse_args()
    if args.destination is None:
        dest = "/data_2/transcode/output"
    else:
        dest = args.destination

#    rec = Recorded(data=[chanid, starttime])
    rec = Recorded(args.findid)
    filename = gen_link(rec, dest)
    
    
    xml = ET.Element('VideoFile')
    ET.SubElement(xml,'path').text = os.path.dirname(filename)
    ET.SubElement(xml,'basename').text = os.path.basename(filename)
    
    # estimate framerate
    rate = float(rec.seek[-1].mark)/float((rec.endtime-rec.starttime).seconds)
    rates = [24000./1001.,25,30000./1001.,50,60000./1001.]
    diff = [abs(f-rate) for f in rates]
    rate = rates[diff.index(min(diff))]
    print("Framerate:",rate)
    
    uncutlist = ET.SubElement(xml,'uncutlist')
    markup = rec.markup.getuncutlist()
    for cut in range(0, len(markup)):
        ET.SubElement(uncutlist,'cut').text = str(markup[cut][0]/rate)
        ET.SubElement(uncutlist,'cut').text = str(markup[cut][1]/rate)
    
    xmlTree=ET.ElementTree(xml)
    xmlFilename = os.path.basename(filename)+".xml"
    xmlTree.write(xmlFilename,'UTF-8')
    #pretty_string = ET.tostring(xmlTree, pretty_print=True)
    #outfile = open(xmlFilename, "w", encoding="utf-8")
    #outfile.write(pretty_string)
    sys.exit(0)    
    
    
    

#!/usr/bin/env python3
"""
This python script encodes a video for Samsung Galaxy S5 Mini 

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

import subprocess
import os
import sys
import argparse
import re
import xml.etree.ElementTree as ET
import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

#-------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
#-------------------------------------------------------------------------------

# controls the quality of the encode
CRF = '21'

# h.264 profile
PROFILE = 'baseline'

# encoding speed:compression ratio
PRESET = 'slow'

# path to ffmpeg bin
FFMPEG_PATH = 'D:\\tmp\\ffmpeg.exe'

# path to ffprobe bin
FFPROBE_PATH = 'D:\\tmp\\ffprobe.exe'

# path to temp directory
TEMPDIR = 'tmp'

#-------------------------------------------------------------------------------
# encoding script
#-------------------------------------------------------------------------------

def encode(input,output,start=None,duration=None,volume=None,resolution=None,device='default.xml'):
    if device == None:
        device='default.xml'
    try:
        xml = ET.ElementTree(file=device)
    except FileNotFoundError:
        print ("File",device,"not found")
        sys.exit(1)
    video = xml.find('video')
    crf = video.findtext('crf',default=CRF)
    profile = video.findtext('profile',default=PROFILE)
    vcodec = video.findtext('codec',default='libx264')
    lines = int(video.findtext('lines',default='720'))
    
    audio = xml.find('audio')
    acodec = audio.findtext('codec',default='libmp3lame')    
    abitrate = audio.findtext('bitrate',default='192k')
    channels = int(audio.findtext('channels',default='2'))
     
    try:
        command = [FFMPEG_PATH]

        # Input file
        command += [ '-i', input]
        
        if start is not None:
            command += [ '-ss', str(start)]
            
        if duration is not None:
            command += [ '-t', str(duration)]
        
        # Video codec
        command += [ '-y', '-c:v', vcodec, '-preset', PRESET, '-profile:v', profile, '-crf', crf]
        
        # Create filter string
        filters = ['yadif']
        if (resolution == None) or (resolution[1] > lines):
            scaleFilter = 'scale='+str(lines)+'*dar:'+str(lines)
            filters += [scaleFilter]
        command += ["-vf",','.join(filters)]

        command += ['-c:a', acodec, '-b:a', abitrate, '-ac', str(channels)]
      
        # Create filter string
        if volume:
            filters = ['volume='+str(volume)+'dB']
            command += ["-af",','.join(filters)]
        
        command += [output]
        print(command)
        subprocess.call(command)                # encode the video!
    except:
        print("Error encoding:",input)
#    finally:
        # always cleanup even if there are errors

def encodeCopyConcat(output):
    try:
        command = [FFMPEG_PATH]
        command += [ '-f' , 'concat' , '-i', os.path.join(TEMPDIR,"concat.txt"),
            '-y', '-c:v', 'copy', '-c:a', 'copy', '-map',  '0' , '-sn']
        command += [output]
        print(command)
        subprocess.call(command)                # encode the video!
    except:
        print("Error encoding:",input)

class videoFile():
    def __init__(self):
        self.xmlFile = StringVar()
        self.probe = None
        self.path = None

    def parseXmlFile(self):
        try:
            xml = ET.ElementTree(file=self.xmlFile.get())
        except FileNotFoundError:
            print ("File",self.xmlFile.get(),"not found")
            sys.exit(1)
        self.xmlPath = xml.find('path').text
        self.basename = xml.find('basename').text
        uncutlist_xml = xml.find('uncutlist')
        startstoplist = list(uncutlist_xml.iter())
        self.uncutlist = []
        self.start = startstoplist[1].text
        self.stop = None
        for x in range(1,len(startstoplist),2):
            if x+1 < len(startstoplist):
                self.uncutlist.append([startstoplist[x].text,startstoplist[x+1].text])
                self.stop = startstoplist[x+1].text
            else:
                self.uncutlist.append([startstoplist[x].text,None])
                self.stop = None        
        self.probe = None
        #self.input = os.path.join(path,basename)

    def setXmlFile(self, val):
        self.xmlFile.set(val)
        self.parseXmlFile()

    def setSourcePath(self, val):
        self.path=val
        self.probe = None

    def getBasename(self):
        return self.basename

    def setBasename(self, val):
        if self.basename != val:
            self.probe = None
            self.basename=val

    def getSourcePath(self):
        return self.path

    def getXmlPath(self):
        return self.xmlPath

    def probeInputFile(self):
        if self.probe == None:
            command= [FFMPEG_PATH, '-i', os.path.join(self.path,self.basename)]
            if self.start is not None:
                command += [ '-ss', self.start]
                if self.stop is not None:
                    command += [ '-t', str(float(self.stop)-float(self.start))]
            command += [ '-vn', '-sn', '-af', 'volumedetect', '-f', 'null', '/dev/null']
            result=subprocess.run(command,stderr=subprocess.PIPE)
            self.probe=result.stderr.decode("utf-8") 

    def getVolume(self):
        self.probeInputFile()
        try:
            match=re.findall("max_volume: (.*) dB",self.probe)
            volume=[float(x) for x in match]
            volume.sort()
        except:
            volume=None
        self.volume = volume[0] * -1
        return self.volume

    def setVolume(self, val):
        self.volume = float(val)
        print("Set volume to",val)

    def encode(self, val):
        output = val.get()
        if len(self.uncutlist) == 0:
            encode(os.path.join(self.path,self.basename),output,resolution=None,volume=self.volume)
        else:
            concat_file = open(os.path.join(TEMPDIR,"concat.txt"), "w", encoding="utf-8")
            for x in range(len(self.uncutlist)):
                tempname = "temp_"+str(x)+".mkv"
                tempname = os.path.join(TEMPDIR, tempname)
                concat_string="file '"+tempname+"'\n"
                concat_file.write(concat_string)
                if self.uncutlist[x][1] == None:
                    length = None
                else:
                    length = float(self.uncutlist[x][1]) - float(self.uncutlist[x][0])
                encode(os.path.join(self.path,self.basename),tempname,resolution=None,start=self.uncutlist[x][0],duration=length,volume=self.volume)
            concat_file.close()
            encodeCopyConcat(output)
        
class mainWindow(tkinter.Tk):
    def __init__(self,parent):
        tkinter.Tk.__init__(self,parent)
        self.parent = parent 
        self.initialize()
        
    def browseXmlFile(self):
        self.setXmlFile(filedialog.askopenfilename(title='Input file (xml)',filetypes=[('xml files', '.xml')]))
    
    def setXmlFile(self, val):
        self.xmlFile.set(val)
        self.videoFile = videoFile()
        self.videoFile.setXmlFile(val)
        self.sourcePath.set(self.videoFile.getSourcePath())
        self.basename.set(self.videoFile.getBasename())

    def browseSourcePath(self):
        self.setSourcePath(filedialog.askdirectory(title='Path to input video files'))

    def setSourcePath(self, val):
        self.videoFile.setSourcePath(val)
        self.sourcePath.set(val)

    def sourcePathFromXml(self):
        self.sourcePath.set(self.videoFile.getXmlPath())

    def browseOutputFile(self):
        self.output.set(filedialog.asksaveasfilename(title='output video file',filetypes=[('MKV files', '.mkv'), ('MP4 files', '.mp4'), ('MPG files', '.mpg')]))

    def setOutputFile(self, val):
        self.output.set(val)

    def calculateVolume(self):
        self.videoFile.setBasename(self.basename.get())
        if len(self.sourcePath.get()):
            self.videoFile.setSourcePath(self.sourcePath.get())
        self.volume.set(self.videoFile.getVolume())

    def encode(self):
        self.videoFile.setBasename(self.basename.get())
        try:
            if float(self.volume.get()) < 0:
                self.videoFile.setVolume(float(self.volume.get()))
            else:
                self.videoFile.setVolume(0)
        except:
            self.videoFile.setVolume(0)
        self.videoFile.encode(self.output)        
        
    def initialize(self):
        self.sytle = ttk.Style()
        frame = ttk.Frame(self,padding="3 3 12 12")
        frame.grid(column=0, row=0, sticky=(N, W, E, S))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self.videoFile = videoFile()

        self.xmlFile = StringVar()
        ttk.Label(frame, text="Input XML file:").grid(column=1, row=1, sticky=(E))
        ttk.Label(frame, textvariable=self.xmlFile).grid(column=2, row=1, sticky=(W, E))
        ttk.Button(frame, text="Browse", command=self.browseXmlFile).grid(column=3, row=1, sticky=W)

        self.sourcePath = StringVar()
        self.setSourcePath("input")
        ttk.Label(frame, text="Path to input video files:").grid(column=1, row=2, sticky=(E))
        ttk.Label(frame, textvariable=self.sourcePath).grid(column=2, row=2, sticky=(W, E))
        ttk.Button(frame, text="Browse", command=self.browseSourcePath).grid(column=3, row=2, sticky=(W, E))
        ttk.Button(frame, text="From XML", command=self.sourcePathFromXml).grid(column=4, row=2, sticky=W)
        
        self.basename = StringVar()
        ttk.Label(frame, text="Basename:").grid(column=1, row=3, sticky=(E))
        #ttk.Label(frame, textvariable=self.basename).grid(column=2, row=3, sticky=(W, E))
        ttk.Entry(frame, textvariable=self.basename).grid(column=2, row=3, sticky=(W, E))
        
        self.output = StringVar()
        ttk.Label(frame, text="Output video file:").grid(column=1, row=4, sticky=(E))
        ttk.Label(frame, textvariable=self.output).grid(column=2, row=4, sticky=(W, E))
        ttk.Button(frame, text="Browse", command=self.browseOutputFile).grid(column=3, row=4, sticky=W)
        
        self.device = StringVar()
        self.device.set('Galaxy S5 Mini')
        ttk.Label(frame, text="Device:").grid(column=1, row=5, sticky=(E))
        ttk.Combobox(frame, textvariable=self.device, values=['Galaxy S5 Mini']).grid(column=2, row=5, sticky=(W))
        
        self.volume = StringVar()
        ttk.Label(frame, text="Volume (dB):").grid(column=1, row=6, sticky=(E))
        volumeEntry = ttk.Entry(frame, textvariable=self.volume).grid(column=2, row=6, sticky=(W, E))
        ttk.Button(frame, text="Calculate", command=self.calculateVolume).grid(column=3, row=6, sticky=W)
        
        ttk.Button(frame, text="Encode", command=self.encode).grid(column=2, row=7)
        
     
if __name__ == "__main__":
    summary="Summary:\n"
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Encode a video')
    parser.add_argument('-i', help='xml-file describing input file')
    parser.add_argument('-o', help='output video file')
    parser.add_argument('-path', help='overwrites path value in input file')
    #parser.add_argument('--device', help='XML file specifying device settings')
    args = parser.parse_args()
 
    app = mainWindow(None)
    app.title("Transcode Video")
 
    print(args.i)
    if args.i:
        app.setXmlFile(args.i)
    else:
        app.browseXmlFile()
        
    if args.o:
        app.setOutputFile(args.o)
    else:
        app.browseOutputFile()

    if args.path:
        app.setSourcePath(args.path)
    else:
        app.setSourcePath(os.getcwd())
    
    app.mainloop()
    
    sys.exit(1)

    # getting resolution
    match=re.search("(\d{3,4})x(\d{3,4})",probe)
    if match:
        resolution=[int(match.group(1)),int(match.group(2))]
        summary+="Resolution: "+match.group(0)+"\n"
    else:
        resolution=None

    


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
            volume = volume * -1 
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
        
if __name__ == "__main__":
    summary="Summary:\n"
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Encode a video')
    parser.add_argument('input', help='xml-file describing input file')
    parser.add_argument('output', help='output video file')
    parser.add_argument('--device', help='XML file specifying device settings')
    args = parser.parse_args()
    
    try:
        xml = ET.ElementTree(file=args.input)
    except FileNotFoundError:
        print ("File",args.input,"not found")
        sys.exit(1)
    #except:
        #print ("Error opening file File",args.input)
        #sys.exit(1)       
            
    
    path = xml.find('path').text
    basename = xml.find('basename').text
    uncutlist_xml = xml.find('uncutlist')
    startstoplist = list(uncutlist_xml.iter())
    uncutlist = []
    start = startstoplist[1].text
    stop = None
    for x in range(1,len(startstoplist),2):
        if x+1 < len(startstoplist):
            uncutlist.append([startstoplist[x].text,startstoplist[x+1].text])
            stop = startstoplist[x+1].text
        else:
            uncutlist.append([startstoplist[x].text,None])
            stop = None        

    input = os.path.join(path,basename)
    output = args.output
    summary+="Input: "+input+"\n"
    summary+="Output: "+output+"\n"
    print(input, output)

    # Probing input file
    command= [FFMPEG_PATH, '-i', input]
    if start is not None:
        command += [ '-ss', str(start)]
        if stop is not None:
            command += [ '-t', str(stop-start)]
    command += [ '-vn', '-sn', '-af', 'volumedetect', '-f', 'null', '/dev/null']
    result=subprocess.run(command,stderr=subprocess.PIPE)
    probe=result.stderr.decode("utf-8") 

    # getting max volume
    try:
        match=re.findall("max_volume: (.*) dB",probe)
        volume=[float(x) for x in match]
        volume.sort()
        summary+="Volume: "+str(volume[0])+"\n"
    except:
        volume=None

    # getting resolution
    match=re.search("(\d{3,4})x(\d{3,4})",probe)
    if match:
        resolution=[int(match.group(1)),int(match.group(2))]
        summary+="Resolution: "+match.group(0)+"\n"
    else:
        resolution=None

    if len(uncutlist) == 0:
        encode(input,output,resolution=resolution,device=args.device,volume=volume[0])
    else:
        concat_file = open(os.path.join(TEMPDIR,"concat.txt"), "w", encoding="utf-8")
        for x in range(len(uncutlist)):
            tempname = "temp_"+str(x)+".mkv"
            tempname = os.path.join(TEMPDIR, tempname)
            concat_string="file '"+tempname+"'\n"
            concat_file.write(concat_string)
            if uncutlist[x][1] == None:
                length = None
            else:
                length = int(uncutlist[x][1]) - int(uncutlist[x][0])
            encode(input,tempname,resolution=resolution,start=uncutlist[x][0],duration=length,device=args.device,volume=volume[0])
        concat_file.close()
        encodeCopyConcat(output) 
        print(summary)
        print(resolution[1])
    


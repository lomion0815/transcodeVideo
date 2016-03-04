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
#import os
import argparse
import re

#-------------------------------------------------------------------------------
# CONFIGURABLE SETTINGS
#-------------------------------------------------------------------------------

# controls the quality of the encode
CRF = '21'

# h.264 profile
PROFILE = 'baseline'

# encoding speed:compression ratio
PRESET = 'medium'

# path to ffmpeg bin
FFMPEG_PATH = 'D:\\tmp\\ffmpeg.exe'

# path to ffprobe bin
FFPROBE_PATH = 'D:\\tmp\\ffprobe.exe'

#-------------------------------------------------------------------------------
# encoding script
#-------------------------------------------------------------------------------

def encode(input,output,start=None,duration=None,volume=None,resolution=None):
    try:
        command = [FFMPEG_PATH]
        if start is not None:
            command += [ '-ss', start]
        
        command += [ '-i', input,
            '-y', '-c:v', 'libx264', '-preset', PRESET, '-profile:v', PROFILE, '-crf', CRF,]
        
        if duration is not None:
            command += [ '-t', duration]
        
        # Create filter string
        filters = ['yadif']
        if (resolution == None) or (sorted(resolution)[0] > 720):
            filters += ['scale=720*dar:720']
        command += ["-vf",','.join(filters)]

        command += ['-c:a', 'libmp3lame', '-b:a', '128k', '-ac', '2']
        command += [output]
        print(command)
        subprocess.call(command)                # encode the video!
    except:
        print("Error encoding:",input)
#    finally:
        # always cleanup even if there are errors


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Encode a video for Samsung Galaxy S5 Mini.')
    parser.add_argument('input', help='input video file or textfile (.txt) containing a list of files')
    parser.add_argument('output', help='output video file')
    parser.add_argument('-ss','--start', type=float, help='start time in seconds')
    parser.add_argument('-t','--duration', type=float, help='duration in seconds')
    args = parser.parse_args()
    input = args.input
    output = args.output
    start = args.start
    duration = args.duration

    # Probing input file
    command= [FFMPEG_PATH, '-i', input, '-vn', '-sn', '-af', 'volumedetect', '-f', 'null', '/dev/null']
    result=subprocess.run(command,stderr=subprocess.PIPE)
    probe=result.stderr.decode("utf-8") 
    # getting max volume
    try:
        match=re.findall("max_volume: (.*) dB",probe)
        volume=[float(x) for x in match]
        volume.sort()
    except:
        volume=None
        
    # getting resolution
    try:
        match=re.search("(\\d{3,4})x(\\d{3,4})",probe)
        groups=match.group(1,2)
        resolution=[int(x) for x in groups]
    except:
        resolution=None

    encode(input,output,resolution=resolution)
    


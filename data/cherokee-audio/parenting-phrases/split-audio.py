#!/usr/bin/env python3

import os
import sys
import string
import unicodedata as ud
import random
import re
import pathlib
import subprocess
from shutil import rmtree

workdir:str = os.path.dirname(sys.argv[0])
if workdir.strip() != "":
    os.chdir(workdir)
workdir = os.getcwd()

# https://stackoverflow.com/questions/45526996/split-audio-files-using-silence-detection

# Import the AudioSegment class for processing audio and the 
# split_on_silence function for separating out silent chunks.
from pydub import AudioSegment
from pydub.silence import split_on_silence

# From https://stackoverflow.com/questions/29547218/
# remove-silence-at-the-beginning-and-at-the-end-of-wave-files-with-pydub
from pydub import AudioSegment


def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms
    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0  # ms
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold:
        trim_ms += chunk_size

    return trim_ms

# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)

#clean up any previous files
rmtree("mp3", ignore_errors=True)
os.mkdir("mp3")

from os import walk
files:list = []
for (dirpath, dirnames, filenames) in walk("src"):
    files.extend(filenames)
    break
files.sort()
splits:list=[]
for file in files:
    if os.path.splitext(file)[1].lower()!=".ogg":
        continue
    print(f"Processing {file}")
    data = AudioSegment.from_ogg("src/" + file)
    file=os.path.splitext(file)[0]
    print(" - silence hunting")
    segments = split_on_silence(data, 1200, -34, keep_silence=1200)
    
    if len(segments)==0:
        print(f"=== NO SPLITS FROM: {file}")
        splits.append("src/"+file)
        continue
    
    for i, segment in enumerate(segments):
        # Normalize the entire chunk.
        normalized = match_target_amplitude(segment, -18.0)
        
        # Trim off leading and trailing silence
        start_trim = detect_leading_silence(normalized, silence_threshold=-34)
        end_trim = detect_leading_silence(normalized.reverse(), silence_threshold=-34)
        duration = len(normalized)
        trimmed = normalized[start_trim:duration-end_trim]
        
        print(f"Saving mp3/{file}-{i:03d}.mp3.")
        trimmed.export(f"mp3/{file}-{i:03d}.mp3",bitrate="192k",format="mp3")
        splits.append(f"mp3/{file}-{i:03d}.mp3")

with open("parenting-phrases.txt", "w") as f:
    for mp3 in splits:
        if os.path.splitext(mp3)[1].lower()!=".mp3":
            continue
        f.write("?") #speaker
        f.write("|")
        f.write(mp3) #audio file
        f.write("|")
        f.write("\n")
        
sys.exit()
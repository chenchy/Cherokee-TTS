#!/usr/bin/env python3
import os
import sys
import string
import unicodedata as ud
import random
import re
import pathlib
import subprocess
from pydub import AudioSegment
from shutil import rmtree

MASTER_TEXT:str="aeneas.txt"
LONG_TEXT:str="durbin-feeling-longer-sequences.txt"

# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)

if __name__ == "__main__":
    
    minLength:int=60*40
    
    dname=os.path.dirname(sys.argv[0])
    if len(dname)>0:
        os.chdir(dname)
    
    print("Cleaning up from previous session")
    rmtree("mp3-long", ignore_errors=True)
    pathlib.Path(".").joinpath("mp3-long").mkdir(exist_ok=True)
    
    print("Loading list and calculating total audio length")
    
    haveLength:int=0
    with open(MASTER_TEXT, "r") as f:
        entriesDict: dict = {}
        for line in f:
            spkr: str=line.split("|")[0].strip()
            mp3: str=line.split("|")[1].strip()
            text: str=ud.normalize("NFD", line.split("|")[2].strip())
            if text=="":
                continue
            entriesDict[text]=(mp3,text, spkr)
            
    for e in entriesDict.values():
        haveLength += AudioSegment.from_mp3(e[0]).duration_seconds
            
    if minLength - haveLength > haveLength:
        minLength -= haveLength
    else:
        minLength = haveLength
    minLength=min(minLength, haveLength*2)
        
    startingEntries:list=[e for e in entriesDict.values()]
    
    speakers:set=set([e[2] for e in startingEntries])
    if len(speakers)>1:
        print("Speakers:",speakers)
        
    print(f"Have {len(startingEntries):,} starting entries with {len(speakers):,} speakers.")    
    print(f"Starting audio duration (minutes): {int(haveLength/60)}")
    print(f"Need additional augmented duration (minutes): {int(minLength/60)}")
    
    entries:list=list()
    _:int=0    
    workingLength:int=0
    while workingLength < minLength:
        random.Random(len(entries)).shuffle(startingEntries)
        entries.extend(startingEntries)
        workingLength+=haveLength
    
    print(f"Have {len(entries):,} entries with {len(speakers):,} speakers.")
    print(f"Minimum target duration (minutes): {int((workingLength+haveLength)/60)}")
    
    dice=random.Random(len(entries))
    
    with open(LONG_TEXT, "w") as f:
        f.write("")
        
    totalTime:float=0
    totalCount:int=0
    
    already:list=set()
    
    for speaker in speakers:
        ix:int=0
        if len(speakers)>1:
            print(f"Processing speaker {speaker}")
       
        #First add in all individual entries as is.
        for entry in startingEntries:
            ix+=1
            if entry[2] != speaker:
                continue
            audioData:AudioSegment = AudioSegment.from_mp3(entry[0])
            track:AudioSegment = match_target_amplitude(audioData, -16)
            text:str=entry[1].strip()
            if ix % 100 == 0:
                print(f"... {speaker}: {text} [totalCount={totalCount:,}, {int(ix/len(startingEntries)*100):d}%] / Duration (minutes): {int(totalTime/60)} [se]")
            if speaker+"|"+text not in already:
                    totalTime+=track.duration_seconds
                    totalCount+=1
                    track.export(f"mp3-long/{totalCount:06d}.mp3", format="mp3", bitrate="192")
                    already.add(speaker+"|"+text)
                    with open(LONG_TEXT, "a") as f:
                        f.write(f"{speaker}")
                        f.write("|")
                        f.write(f"mp3-long/{totalCount:06d}.mp3")
                        f.write("|")
                        f.write(ud.normalize("NFC", text))
                        f.write("\n")
    
    for speaker in speakers:
        ix:int=0
        if len(speakers)>1:
            print(f"Processing speaker {speaker}")
        text:str=""
        track:AudioSegment=AudioSegment.empty()
        wantedLen=dice.randint(1, 6)+dice.randint(1, 6)+dice.randint(1, 6)
        for entry in entries:
            ix+=1
            if entry[2] != speaker:
                continue
            audioData:AudioSegment = AudioSegment.from_mp3(entry[0])
            audioText:str = entry[1].strip()
            if ix % 100 == 0:
                print(f"... {speaker}: {audioText} [totalCount={totalCount:,}, {int(ix/len(entries)*100):d}%] / Duration (minutes): {int(totalTime/60)} [ad]")
            if len(audioText)==0:
                continue
            if audioText[-1] not in ".,?!":
                audioText+="."
            if audioData.duration_seconds + track.duration_seconds > wantedLen and track.duration_seconds>0:
                if speaker+"|"+text not in already:
                    totalTime+=track.duration_seconds
                    totalCount+=1
                    track.export(f"mp3-long/{totalCount:06d}.mp3", format="mp3", bitrate="192")
                    already.add(speaker+"|"+text)
                    with open(LONG_TEXT, "a") as f:
                        f.write(f"{speaker}")
                        f.write("|")
                        f.write(f"mp3-long/{totalCount:06d}.mp3")
                        f.write("|")
                        f.write(ud.normalize("NFC", text))
                        f.write("\n")
                text=""
                track=AudioSegment.empty()
                wantedLen=dice.randint(1, 4)+dice.randint(1, 4)+dice.randint(1, 4)
            
            if len(track) > 0:
                track += AudioSegment.silent(500, 22050)
            track += match_target_amplitude(audioData, -16)
            
            if len(text)>0:
                text += " "
            text += audioText
            
        if len(track)>0 and speaker+"|"+text not in already:
            totalTime+=track.duration_seconds
            totalCount+=1
            track.export(f"mp3-long/{totalCount:06d}.mp3", format="mp3", bitrate="192")
            with open(LONG_TEXT, "a") as f:
                    f.write(f"{speaker}")
                    f.write("|")
                    f.write(f"mp3-long/{totalCount:06d}.mp3")
                    f.write("|")
                    f.write(ud.normalize("NFC", text))
                    f.write("\n")
                
    print(f"Total time (minutes): {int(totalTime/60)}")    
    print(f"Total tracks: {totalCount:,}.")
    print(f"Average track time: {totalTime/totalCount:.2f}.")
    print("Folder:",pathlib.Path(".").resolve().name)
    
    #verify all are unique audio file entries
    with open(LONG_TEXT, "r") as f:
        already:set=set()
        for line in f:
            fields=line.split("|")
            if fields[1] in already:
                print(f"FATAL: DUPLICATE AUDIO FILE ENTRY: {line}")
                sys.exit(-1)
            already.add(fields[1])
        print(f"All entries test as unique.")
    
    sys.exit(0)
    
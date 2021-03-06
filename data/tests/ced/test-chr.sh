#!/bin/bash

set -e
set -o pipefail

cd "$(dirname "$0")"
z="$(pwd)"

rm *.npy 2> /dev/null || true
rm *.wav 2> /dev/null || true

cd ../../..
y="$(pwd)"

source ~/miniconda3/etc/profile.d/conda.sh

conda activate ./env

cp="$(ls -1tr checkpoints/|tail -n 1)"

printf "Using checkpoint: $cp\n"

tmp="$z/tmp.txt"
selected="$z/selected.txt"
cp /dev/null "$tmp"

for x in "$z"/ced-[0-9][0-9]-*; do
	if [ ! -d "$x" ]; then continue; fi
	rm -r "$x"
done

v=("01-chr" "02-chr" "03-chr" "04-chr" "05-chr")
vsize="${#v[@]}"

printf "\nTotal voice count: %d\n\n" "$vsize"

wg="ced"
text="$z/../../cherokee-syn/syn-chr.txt"

cut -f 7 -d '|' "$text" | grep -v ' ' | shuf | tail -n 10 | sort > "$selected"

for voice in "${v[@]}"; do
	printf "Generating audio for %s\n" "$voice"
	ix=0
	syn=""
	cp /dev/null "$tmp"
	cat "$selected" | while read phrase; do
		ix=$(($ix+1))
		printf "%d|%s|%s|chr\n" "$ix" "${phrase}" "$voice" >> "$tmp"
	done

	cd "$y"
	
	cat "$tmp" | python synthesize.py --output "$z/" --save_spec --checkpoint "checkpoints/$cp" --cpu

	cd "$z"
	
	rm -r "$wg"-"$voice" 2> /dev/null || true
	mkdir "$wg"-"$voice"
	cp -p "$selected" "$wg"-"$voice"
	
	python wavernnx-cpu.py
	#python wavernnx.py

	mv wg*.wav "$wg"-"$voice"/
	xdg-open "$wg"-"$voice"
	
	ix=0
	cat "$selected" | while read line; do
		ix="$(($ix+1))"
		rm "$ix".wav || true
		rm "$ix".npy || true
	done
	printf "\n\n"
done

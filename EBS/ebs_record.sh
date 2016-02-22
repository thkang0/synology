#!/bin/bash 
RADIO_ADDR="rtmp://ebsandroid.ebs.co.kr:1935/fmradiofamilypc/familypc1m"

PROGRAM_NAME=$1 
RECORD_MINS=$(($2 * 60)) 
DEST_DIR=$3 

REC_DATE=`date +%Y%m%d-%H%M` 
TEMP_FLV=`mktemp -u` 

#OUTPUT_FILENAME=$PROGRAM_NAME"_"$REC_DATE.m4a 
OUTPUT_FILENAME=$REC_DATE.m4a 

rtmpdump -r $RADIO_ADDR -B $RECORD_MINS -o $TEMP_FLV 
#ffmpeg -i $TEMP_FLV -vn -acodec copy $OUTPUT_FILENAME > /dev/null 2>&1 
avconv -i $TEMP_FLV -vn -acodec copy $OUTPUT_FILENAME > /dev/null 2>&1 

rm $TEMP_FLV 

mkdir -p $DEST_DIR 
mv $OUTPUT_FILENAME $DEST_DIR

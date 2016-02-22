#!/bin/sh 
PROGRAM_NAME=$1
RECORD_TIME=$2

find ./$PROGRAM_NAME -mtime +7 -exec rm {} \;

CHROOTTARGET=/usr/local/debian-chroot/var/chroottarget 
#grep -q "${CHROOTTARGET}/mnt/public " /proc/mounts || mount -o bind /volume1/EBS ${CHROOTTARGET}/mnt/public 
mount | grep -q "/volume1/EBS" || mount -o bind /volume1/EBS ${CHROOTTARGET}/mnt/public
chroot ${CHROOTTARGET} /mnt/public/ebs_record.sh $PROGRAM_NAME $RECORD_TIME /mnt/public/$PROGRAM_NAME

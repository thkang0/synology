#! /bin/sh

checkStatus=`ps | grep -v grep | grep -q dsmonitor || echo $?`  
echo $checkStatus 

if [ "$checkStatus" -eq "0" ]
then                                                                 
    echo "There is monitoring shell running"                                                                                
    exit                                                                                                                    
else
    echo "There is no monitoring shell"
    /bin/bash -c /volume1/homes/admin/dsmonitor.sh &
fi                                                                                                                          
          

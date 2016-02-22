#!/bin/sh
 
myOption=$1
  
if [ "${myOption}"="" ]
then
##echo "Reindex Option: video | music | photo | playlist | all(default)"
    myOption="all"
fi

date "+%Y.%m.%d %H:%M:%S"
echo "/usr/syno/bin/synoindex -R ${myOption}"

/usr/syno/bin/synoindex -R ${myOption}
returnCode=$?
             
if [ ${returnCode} -ne 0 ]
then
    echo "Error: ${returnCode}"
else
    echo "Completed!!!"
fi

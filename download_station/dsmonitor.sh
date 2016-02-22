#! /bin/sh

currentDate=$(date "+%Y/%m/%d %H:%M:%S")
startMsg="${currentDate}%0ADS DonwloadStation Monitor 서비스가 시작되었습니다."

curl "https://api.telegram.org/bot<your_key_token>/sendMessage?chat_id=<your_chat_id>&text=$startMsg"

while :
do

    psql -U postgres -d download -t -A -c "SELECT * FROM btdownload_event;" | while  read line
    do
        IDX=`echo $line | cut -d '|' -f1`
        USER_NAME=`echo $line | cut -d '|' -f2`
        TITLE=`echo $line | cut -d '|' -f3`
        STATUS_VALUE=`echo $line | cut -d '|' -f4`
        SIZE=`echo $line | cut -d '|' -f5`
        CREATE_TIME=`echo $line | cut -d '|' -f7`

        DOWNLOAD_QUEUE=$(psql -U postgres -d download -t -A -c "SELECT * FROM download_queue WHERE task_id=$IDX")
        DOWNLOADING=`echo $DOWNLOAD_QUEUE | cut -d '|' -f6`        
        
        if [ "$DOWNLOADING" -eq "8" ]
        then
            psql -U postgres -d download -c "DELETE FROM btdownload_event WHERE task_id=$IDX"
            STATUS_VALUE=5
            
	    case $STATUS_VALUE in
                1) STATUS="대기 중" ;;
                2) STATUS="다운로드 중" ;;
                3) STATUS="일시 정지" ;;
                4) STATUS="종료 중" ;;
                5) STATUS="다운로드 완료" ;;
                6) STATUS="해시 체크" ;;
                7) STATUS="시딩 중" ;;
                8) STATUS="파일 호스팅 대기" ;;
                9) STATUS="압축 해제 중" ;;
                *) STATUS="알 수 없는 코드 [$STATUS_VALUE]" ;;
            esac
		
            CONV_SIZE=`echo $SIZE | awk '{ sum=$1 ; hum[1024**3]="GB";hum[1024**2]="MB";hum[1024]="KB"; for (x=1024**3; x>=1024; x/=1024){ if (sum>=x) { printf "%.2f %s\n",sum/x,hum[x];break } }}'`
    
	    currentStatus="상태   : ${STATUS}%0A파일   : ${TITLE}%0A크기   : ${CONV_SIZE}%0A사용자 : ${USER_NAME}"
	    echo $currentStatus
            curl -d "chat_id=<your_chat_id>&text=$currentStatus" "https://api.telegram.org/bot<your_key_token>/sendMessage"
        elif [ "$DOWNLOADING" -eq "2" ]
        then
            psql -U postgres -d download -t -A -c "SELECT * FROM btdownload_event WHERE isread=0;" | while  read second_line
            do 
                echo $second_line
                NEW=`echo $second_line | cut -d '|' -f1`
                USER=`echo $second_line | cut -d '|' -f2`
                NAME=`echo $second_line | cut -d '|' -f3`
                SIZE2=`echo $second_line | cut -d '|' -f5`
                psql -U postgres -d download -c "UPDATE btdownload_event SET isread = 1 WHERE task_id = $NEW" 
                CONV_SIZE=`echo $SIZE2 | awk '{ sum=$1 ; hum[1024**3]="GB";hum[1024**2]="MB";hum[1024]="KB"; for (x=1024**3; x>=1024; x/=1024){ if (sum>=x) { printf "%.2f %s\n",sum/x,hum[x];break } }}'`

                STATUS="다운로드 중"
                currentStatus="상태   : ${STATUS}%0A파일   : ${NAME}%0A크기   : ${CONV_SIZE}%0A사용자 : ${USER}"
                curl -d "chat_id=<your_chat_id>&text=$currentStatus" "https://api.telegram.org/bot<your_key_token>/sendMessage"
            done
        fi
    done

    sleep 5
done

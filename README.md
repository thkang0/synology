# Scripts for Synology 
시놀로지를 보다 잘 이용하기 위해서 스크립트와 텔레그램 알림, TV 수신카드를 통해 TV수신 등을 하기 위한 설정, 파일

# Telegram Notification
1. 텔레그램 bot을 만들고, 챗 아이디와 키 토큰을 얻는다.
   https://nas.moe/archives/879
2. telegram.php를 웹서버 위치에 복사 한다. 
   예) /volume1/web/telegram.php
3. Disk Station에서 제어판 -> 알림 항목에 가서 위 링크에 따라 수정한다.

# Telegram Notification with Download Station
1. 아래 링크와 같이 download station의 psql 데이터베이스에 모니터링을 위한 테이블과 트리거 함수를 생성한다.
   https://nas.moe/archives/913
2. 테스트를 해보니 다운로드 시작 알림은 오는데 완료 알림은 오지 않아 스크립트를 조금 수정하였음.
   run_monitor.sh : download station 스크립트를 체크 함 ==> 작업 스케쥴러에 등록하거나 crontab에 등록해서 사용. 그리고 스크립트 안의 /bin/bash -c /volume1/homes/admin/dsmonitor.sh & 부분은 위치에 따라 수정 필요
   dsmonitor.sh : key token과 chat id는 본인에 맞게 넣어줘야 함

# EBS 라디오 녹음하기
1. debian chroot를 설치 :  http://packages.synocommunity.com/  소스를 패키지 센터에 추가
2. EBS 공유 폴더 생성
3. root계정으로 접속하여 chroot /usr/local/debian-chroot/var/chroottarget /bin/bash 실행
4. apt-get update; apt-get install rtmpdump libav-tools
5. debian chroot를 나간 후 디렉토리 마운트
   - 시놀로지의 EBS 디렉토리로 마운트 할 디렉토리 작성
       mkdir /usr/local/debian-chroot/var/chroottarget/mnt/public
   - 마운트 
       mount /volume1/EBS /usr/local/debian-chroot/var/chroottarget/mnt/public
6. EBS 디렉토리에 ebs_record.sh re-index.sh schedule_record.sh 파일 복사 (실행 권환 확인)
7. 제어판 작업 스케쥴러에서 해당되는 라디오 시간에 맞추어 schedule_record.sh 스크립트 수행 (7일이 지난 데이터는 삭제 됨)
   예) /volume1/EBS/schedule_record.sh easy_writing 20 ==> 이지 라이팅 라디오를 20분동안 녹음한다.
8. Audio station과 연동하기 위해 제어판의 미디어 색인 부분에 EBS 디렉토리를 추가하고, re-index.sh 스크립트를 라디오 스케쥴이 끝나고 난 후 수행한다.(작업 스케쥴러에 등록)

# tvheadend : http://syno.dierkse.nl
1. EPG 등록 : https://nas.moe/archives/1010
2. 채널 등록 : https://nas.moe/archives/858
   - DVB Inputs -> Networks -> Add ATSC 한 후 네트워크를 생성
   - Muxes -> Add : 아래 숫자의 주파수, VSB/8로 생성 (서울/경기 지역 해당)

        A 267012500 8VSB #GMTV, 쿠키건강TV, noll TV
        A 291012500 8VSB #JTBC3, SPOTV+, Etn, GMTV, 쿠키건강TV, nollTV
        A 297012500 8VSB #리빙TV, 어린이TV, EBS+2, 재능잉글리쉬, 하이라이트TV, FunTV
        A 303012500 8VSB #재능잉글리쉬, 하이라이트TV, FunTV, 리빙TV, 어린이TV, EBS+2
        A 309012500 8VSB #인디필름, CNN, NHK
        A 315012500 8VSB #채널J, GTV
        A 321012500 8VSB #CNTV, SBS FunE
        A 333025000 8VSB #DramaH
        A 345012500 8VSB #I.Net, 챔프, 리얼TV
        A 351012500 8VSB #국회방송, CJ오쇼핑
        A 357012500 8VSB #NS홈쇼핑, 현대홈쇼핑
        A 363012500 8VSB #GS홈쇼핑, 롯데홈쇼핑
        A 369012500 8VSB #MBN, JTBC
        A 375012500 8VSB #홈엔쇼핑, TV조선
        A 381012500 8VSB #채널A, 뉴스Y
        A 387012500 8VSB #TVN, YTN
        A 393012500 8VSB #OCN, CGV
        A 399012500 8VSB #드라마큐브, SBS드라마
        A 405000000 8VSB #아임쇼핑, 스크린
        A 411000000 8VSB #KBS드라마, MBC드라마
        A 417000000 8VSB #AXN, XTM
        A 423000000 8VSB #드라맥스, Fox
        A 429000000 8VSB #MBC에브리원, KBS Joy
        A 435000000 8VSB #E채널, Q티비
        A 447000000 8VSB #TLC, MBC뮤직
        A 453000000 8VSB #Mnet, KBS스포츠
        A 459000000 8VSB #MBC, SBS스포츠
        A 465000000 8VSB #MBC퀸, KBS W
        A 471000000 8VSB #SuperAction, JTBC 골프
        A 477000000 8VSB #아리랑TV, SBS골프
        A 483000000 8VSB #OnStyle, HD디스커버리
        A 489000000 8VSB #TVB, CMB
        A 495000000 8VSB #육아, 코미디TV, OBS
        A 507000000 8VSB #투니버스, 재능TV, 에듀키즈
        A 513000000 8VSB #애니맥스, 카툰네트워크, 토마토TV
        A 519000000 8VSB # EBS+1, 애니박스, 한국경제TV
        A 525000000 8VSB #서울경제 & 이데일리 & MTN
        A 531000000 8VSB #SBS CNBC & 복지TV & 아시아경제
        A 537000000 8VSB #CBS & CTS & PBC
        A 543000000 8VSB #BTN & C'Time & OUN
        A 549000000 8VSB #KTV & Egde TV & M Mondey
        A 555000000 8VSB #KBS2
        A 561000000 8VSB #EBS
        A 567000000 8VSB #MBC
        A 573000000 8VSB #KBS1
        A 579000000 8VSB #SBS
3. 백업
   cd  /volume1/@appstore/tvheadend-4.0/var
   tar czvf tvheadend_backup_0201.tar.gz channel/ epggrab/ input/        
4. 맥에서 VLC로 연동
   - copy libhtsp_plugin.dylib to vlc application directory (Contents -> MacOS -> plugins)
   - 설정 -> 모두 보기 -> 재생목록 -> 서비스 검색 -> HTSP Protocol : 서버 ip와 계정, 비번만 넣어주면 됨

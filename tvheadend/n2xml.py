#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
from xml.sax.saxutils import escape
import requests
from datetime import date, timedelta
import re
import json
import argparse
import socket
import encodings.idna
# from string import digits
import codecs
from multiprocessing.dummy import Pool
# from multiprocessing import cpu_count
from functools import partial



default_channel_enabled=0
default_xml_socket='/home/hts/.hts/tvheadend/epggrab/xmltv.sock'
default_fetch_limit=3
default_xml_filename='xmltv.xml'
default_configfile='n2xml.conf'
default_chanfile='chanlist.json'
default_options='-a -l3 -w'
http_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
    }

if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

def err(*objs):
    print("Error:", *objs, file=sys.stderr)

def printLog(*objs):
    if args.outputfile or args.socket:
        print(*objs)
    else:
        print(*objs, file=sys.stderr)

def VERBOSE(*objs):
    if args.verbose:
        printLog(*objs)

def getBroadcastTypeList():
    params = {'broadcastType': 100}
    return re.findall('{broadcastType:(\d+)', req.get('http://tvguide.naver.com/program/multiChannel.nhn', params=params, headers=http_headers).text)

def getChannelGroupList(bid=0, region=0):
    gList={}
    if not bid:
        blist=getBroadcastTypeList()
    else:
        blist=[bid]
    for i in blist:
        if i == '100' and region:
            gList[region] = '지상파'
            continue
        params = { 'broadcastType' : i }
        res = req.post('http://tvguide.naver.com/api/channelGroup/list.nhn', data=params, headers=http_headers).json()
        for r in res['result']:
            if i == '100' and not bid:
                gList[r['channelGroupNo']] = '지상파 (%s)' % r['channelGroupName']
            # 지상파/종편 중복.    
            elif i == '300' and (r['channelGroupNo'] == 25 or r['channelGroupNo'] == 47):
                continue
            else:
                gList[r['channelGroupNo']] = r['channelGroupName']

    return gList

def getChannelList(region=0):
    cList={}
    for i in getChannelGroupList(region=region).items():
        params = { 'channelGroupNo' : i[0] }
        res = req.post('http://tvguide.naver.com/api/channel/list.nhn', data=params, headers=http_headers).json()
        for c in res['result']:
            if str(c['id']) in cList:
                # 채널이 있으면 처리않음, 그룹 분산 방지.
                continue
            cList[str(c['id'])] = { "id": c['id'], "group": i[0], "name": c['name'], "genre": i[1] }

    return cList

def update_chanlist(region=0):
    if not region:
        print("지역을 선택하세요.")
        for i in getChannelGroupList(bid=100).items():
            print("{:>2}: {}".format(str(i[0]), i[1]))
        sys.exit(1)    
    
    try:
        oldlist = json.load(codecs.open(chanfile, 'r', 'utf-8-sig'))

        if 'id' not in list(oldlist.values())[0]:
            for i in list(oldlist):
                oldlist[i] = {'epgid': oldlist[i][5], 'enabled': oldlist[i][6]}
    except:
        oldlist = {}

    newlist = getChannelList(region)
    for i in newlist:
        if i in oldlist:
            # do oldlist stuff here.
            newlist[i].update({'epgid': oldlist[i]['epgid'], 
                                'enabled': oldlist[i]['enabled'],
                                'name': oldlist[i]['name']})
        else:
            # newlist[i].update({'epgid': i, 'enabled': default_channel_enabled})
            newlist[i].update({'epgid': i, 'enabled': args.enabletoggle})

    oldset=set(oldlist.keys())
    newset=set(newlist.keys())
    intersect=newset.intersection(oldset)
    removed=0
    added=0
    for i in oldset-intersect:
        printLog('삭제:', i, oldlist[i]['name'])
        removed += 1
    for i in newset-intersect:
        printLog('추가:', i, newlist[i]['name'])
        added += 1

    if removed or added:
        # json.dumps + replace is easier to read than json.dump+indent
        try:
            f = codecs.open(chanfile+'.new', "w+", encoding="utf8")
            f.write(json.dumps(newlist, ensure_ascii=False, sort_keys=True).replace('{"', '{\r\n"', 1).replace('}, ', '},\r\n').replace('}}', '}\r\n}\r\n').replace(', "', ',  "'))
            f.close()
    
            if oldlist:
                try:
                    os.remove(chanfile+'.bak')
                except:
                    pass
                os.rename(chanfile, chanfile+'.bak')
            os.rename(chanfile+'.new', chanfile)
        except Exception as msg:
            err(msg)
            sys.exit(1)
        # print('삭제:', removed, ', 추가:', added)
    else:
        print('채널 변동이 없습니다.')


def loadChanlist():
    try:
        j = json.load(codecs.open(chanfile, 'r', 'utf-8-sig'))
    except:
        print(chanfile+"이 없습니다. '"+ sys.argv[0]+ " -u'를 실행하세요.")
        sys.exit(1)

    return j

# returns { 'groups': [ groups list ], 'channels': { chanid : groupid, chanid : groupid ... } }
def enabledGroupsAndChannels(l=[]):
    g=set()
    c={}
    if l:
        for i in l:
            try:
                g.add(chanlist[str(i)]['group'])
                c[int(i)] = chanlist[str(i)]['group']
            except KeyError as msg:
                err(msg, '채널이 없습니다.')
                sys.exit(1)
    else:
        for i in chanlist.values():
            if i['enabled']:
                g.add(i['group'])
                c[i['id']] = chanlist[str(i['id'])]['group']

    return dict({ 'groups' : sorted(g), 'channels' : c })


def getGenre(g):
    return {
        "A": "드라마",
        "B": "영화",
        "C": "만화",
        "D": "오락/연예",
        "E": "스포츠",
        "F": "취미/레저",
        "G": "음악",
        "H": "교육",
        "I": "뉴스",
        "J": "시사/다큐",
        "K": "교양/정보",
        "L": "홈쇼핑",
        "M": "TBD:M",
        "N": "TBD:N",
        "O": "TBD:O",
        "P": "TBD:P"
    }[g]

# id, {p}, %Y%m%d%H%M00, %Y%m%d%H%M00, %Y%m%d
def processProgram(chanid, p, start, end, tomorrow=0):
    prog=[]
    extra=[]

    """
    if not end:
        d=p['beginDate'].split('-')
        end=('{:%Y%m%d}{}00'.format(date(int(d[0]), 6, int(d[2]))+timedelta(days=1), p['endTime'].replace(':','')))
    """
    if not end and tomorrow:
        prog.append('\t<programme start="%s +0900" stop="%s%s00 +0900" channel="%s">\n' % ( start, tomorrow, p['endTime'].replace(':', ''), chanlist[str(chanid)]['epgid']))
    else:
        prog.append('\t<programme start="%s +0900" stop="%s +0900" channel="%s">\n' % ( start, end, chanlist[str(chanid)]['epgid']))

    if p.get('subtitle'):
        # 부제, 제대로 처리하는 앱이 없어 제목에 추가.
        # prog.append('\t\t<sub-title lang="kr">%s</sub-title>\n' % p['subtitle'])
        title='%s - %s' % (p.get('scheduleName').strip(), p['subtitle'].strip())
    else:
        title=p.get('scheduleName').strip()
    # prog.append('\t\t<title lang="kr">%s' % title.replace('<','[').replace('>',']').replace('&', '&amp;'))
    prog.append('\t\t<title lang="kr">%s' % escape(title))

    # caption 자막방송
    # signLanguage 수화방송
    # ageRating: integer
    if not args.noextra:
        if p.get('hd'):
            extra.append('[HD]')
        if p.get('live'):
            extra.append('[생]')
        elif p.get('rebroadcast'):
            extra.append('[재]')
        if extra:
            extra.insert(0, ' ')
            prog.append(''.join(extra))
    # prog.append('</title>\n\t\t<category lang="ko">%s</category>\n' % getGenre(p.get('largeGenreId', 'ZZ')))
    prog.append('</title>\n\t\t<category lang="ko">%s</category>\n' % getGenre(p['largeGenreId']))

    if p.get('rebroadcast'):
        prog.append('\t\t<previously-shown />\n')
    
    """ Don't need it.
    if args.noextra and p.get('hd'):
        prog.append('\t\t<video>\n'
                    '\t\t\t<aspect>16:9</aspect>\n'
                    '\t\t\t<quality>HDTV</quality>\n'
                    '\t\t</video>\n')
    """

    episode=p.get('episodeNo')
    if episode:
        prog.append('\t\t<episode-num system="onscreen">%s</episode-num>\n' % episode)
        # match=re.match('.*(시즌(\d+)|\D(\d?\d))[ ]*$', p['scheduleName'])
        match=re.match('.*\D(\d?\d)[ ]*$', p['scheduleName'])
        if match:
            prog.append('\t\t<episode-num system="xmltv_ns">%s.%s.</episode-num>\n' % (int(match.group(1))-1, int(episode.replace('회', ''))-1))
        else:
            # prog.append('\t\t<episode-num system="xmltv_ns">.%s.</episode-num>\n' % ''.join(i for i in episode if i in digits))
            prog.append('\t\t<episode-num system="xmltv_ns">.%s.</episode-num>\n' % (int(episode.replace('회', ''))-1))

    prog.append('\t\t<episode-num system="dd_progid">%s</episode-num>\n' 
                '\t\t<episode-num system="masterid">%s</episode-num>\n' 
                % (p['scheduleId'], p['programMasterId']) )

    if p['ageRating']:
        prog.append('\t\t<rating system="VCHIP">\n\t\t\t<value>%s세 이상 시청가</value>\n\t\t</rating>\n' % p['ageRating'])
    else:
        prog.append('\t\t<rating system="VCHIP">\n\t\t\t<value>모든 연령 시청가</value>\n\t\t</rating>\n')

    prog.append('\t</programme>\n')

    return ''.join(prog)


# today/tomorrow: %Y%m%d
# def processGroup(gid, today, tomorrow, target):
def processGroup(li, channels):
    gid=li[0]
    today=li[1]
    tomorrow=li[2]
    params = { 'channelGroup' : gid, 'date': today }
    res = req.get('http://tvguide.naver.com/program/multiChannel.nhn', params=params, headers=http_headers)
    match=re.search('var PROGRAM_SCHEDULES=([^;]+});', res.text, re.MULTILINE)
    # workaround for regex failure which rarely occurs. need to find out what's wrong with it.
    if match:
        js=json.loads(match.group(1))
    else:
        js=json.loads(res.text.partition('PROGRAM_SCHEDULES=')[2].rpartition('};')[0]+'}')

    # json.dump(js, open('tmp.sched', 'w'), ensure_ascii=False, indent=4)
    # js = json.load(open('tmp.sched'))

    doc=[]
    vlog=[]
    for chan in js['channelList']:
        cid=chan['channelId']
        if cid not in channels:
            continue
        if gid != channels[cid]:
            continue

        if args.verbose:
            vlog.append("gid: {:2} | cid: {:3} {:13}\t| day: {} | programs: {}".format(gid, cid, '('+chan['channelName']+')', today, len(chan['programList'])))
        prev={}
        for p in chan['programList']:
            # ymdt='%s%s00' % (p['beginDate'].replace('-', ''), p['beginTime'].replace(':', ''))
            ymdt='%s%s00' % (today, p['beginTime'].replace(':', ''))
            if prev:
                doc.append(processProgram(cid, prev, prevtime, ymdt))
            else: # first item. 
                ymdt='%s%s00' % (chan['channelBeginDate'].replace('-',''), p['beginTime'].replace(':', ''))
            prev=p
            prevtime=ymdt

        # last item of day
        if prev:
            doc.append(processProgram(cid, prev, prevtime, 0, tomorrow))

    return (''.join(doc), '\n'.join(vlog))

def writeXML(d):
    if args.socket:
        xmlfp.send(d.encode('utf-8'))
    else:
        xmlfp.write(d)

def mainLoop():
    today=date.today()
    dateList=[]
    count=args.limit
    while ( args.limit > 0 ):
        dateList.append('{:%Y%m%d}'.format(today+timedelta(days=args.limit)))
        args.limit += -1
    dateList.append('{:%Y%m%d}'.format(today))
    dateList.reverse()

    target=enabledGroupsAndChannels(args.chans)
    printLog("%s개의 채널 분류에서 %s채널, %s일분의 방송정보를 가져옵니다."
                % (len(target['groups']), len(target['channels']), count) )

    global xmlfp
    try:
        if args.socket:
            VERBOSE("Output:", args.socket)
            xmlfp = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            xmlfp.connect(args.socket)
        elif args.outputfile:
            VERBOSE("Output:", args.outputfile)
            xmlfp = codecs.open(args.outputfile+'.new', "w+", encoding="utf8")
        else:
            VERBOSE("Output: stdout")
            xmlfp = sys.stdout

        writeXML(xmlHeader(args.chans))
        tList=[]
        while ( count > 0 ):
            count += -1
            d=dateList.pop(0)
            for gid in target['groups']:
                tList.append([gid, d, dateList[0]])

        _processGroup = partial(processGroup, channels=target['channels'])
        for res in pool.imap(_processGroup, tList):
            writeXML(res[0])
            VERBOSE(res[1])

        writeXML('</tv>\n')
    except Exception as msg:
        err(msg)
        sys.exit(1)
    finally:
        xmlfp.close()

    if args.outputfile:
        try:
            os.remove(args.outputfile)
        except Exception:
            pass
        os.rename(args.outputfile+'.new', args.outputfile)

def xmlHeader(cList=[]):
    doc=[]
    if args.outputfile:
        doc.append('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
    else:
        import locale
        doc.append('<?xml version="1.0" encoding="%s"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n' % locale.getpreferredencoding())
    doc.append('<tv source-info-url="http://tvguide.naver.com" source-info-name="Naver TV Guide" generator-info-name="n2xml">\n')
    if not cList:
        for i in chanlist.values():
            if i['enabled']:
                doc.append('\t<channel id="%s">\n' % i['epgid'])
                for name in escape(i['name']).split('|'):
                    doc.append('\t\t<display-name>%s</display-name>\n' % name)
                doc.append('\t</channel>\n')
    else:
        try:
            for i in cList:
                doc.append('\t<channel id="%s">\n' % chanlist[i]['epgid'])
                for name in escape(chanlist[i]['name']).split('|'):
                    doc.append('\t\t<display-name>%s</display-name>\n' % name)
                doc.append('\t</channel>\n')

        except KeyError as msg:
            err(msg, '채널이 없습니다.')
            sys.exit(1)

    return ''.join(doc)


def channel_lookup(keyword):
    for i in chanlist.values():
        if keyword in i['name'].lower() or keyword in i['genre'].lower():
            print("{:3}: {} ({}) {}".format(i['id'], i['name'], i['genre'], i['enabled']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    cmds = parser.add_mutually_exclusive_group(required=True)
    cmds.add_argument('-u', type=int, metavar='N', const=0, nargs='?', choices=range(0,11), help='채널 목록 갱신')
    cmds.add_argument('-c', dest='chans', metavar='N', nargs='+', default=[], help='특정 채널(들)의 방송정보 가져오기')
    cmds.add_argument('-a', help='모든 채널의 방송정보 가져오기', action='store_true')
    cmds.add_argument('-f', '--find', metavar='name', help='채널 검색')
    cmds.add_argument('-C', '--config', metavar='설정파일')
    opts = parser.add_argument_group('추가옵션')
    opts.add_argument('-t', dest='thread', type=int, default=4, help=argparse.SUPPRESS)
    opts.add_argument('-p', '--profile', action='store_true', help=argparse.SUPPRESS)
    opts.add_argument('-l', dest='limit', type=int, metavar="1-7", choices=range(1,8), help='가져올 기간, 기본값: '+str(default_fetch_limit), default=default_fetch_limit)
    opts.add_argument('-e', dest='enabletoggle', metavar='1', type=int, choices=[0,1], default=default_channel_enabled, const=1, nargs='?', help='채널 갱신(-u)시 새 채널 활성화')
    opts.add_argument('-N', '--no-extra', dest='noextra', action='store_true', help='[재][HD] 등을 제목에 추가하지 않음')
    opts.add_argument('--chanlist', metavar='file', help='chanlist 파일, 기본값: '+default_chanfile)
    opts.add_argument('-w', dest='outputfile', metavar=default_xml_filename, nargs='?', const=default_xml_filename, help='저장할 파일이름')
    opts.add_argument('-s', dest='socket', metavar=default_xml_socket, nargs='?', const=default_xml_socket, help='xmltv.sock(External: XMLTV)로 EPG정보 전송')
    opts.add_argument('--verbose', action='store_true', help=argparse.SUPPRESS)

    if len(sys.argv) == 1:
        try:
            with open(default_configfile) as f:
                sys.argv.extend(f.read().strip().split())
        except IOError:
            if default_options:
                sys.argv.extend(default_options.split())
        args = parser.parse_args()
        printLog("실행 옵션: %s, 도움말은 %s -h 하세요." % (' '.join(sys.argv[1:]), sys.argv[0]))
    else:
        args = parser.parse_args()
        if args.config:
            del sys.argv[1:]
            try:
                with open(args.config) as f:
                    sys.argv.extend(f.read().strip().split())
                args = parser.parse_args()
                printLog("실행옵션:", ' '.join(sys.argv[1:]))
            except Exception as msg:
                err(msg)
                sys.exit(1)
            
    req = requests.Session()

    if args.chanlist:
        chanfile=args.chanlist
    else:
        chanfile=default_chanfile

    if args.u is not None:
        update_chanlist(args.u)
    chanlist=loadChanlist()

    # 미관(?)상 mutually exclusive group으로 묶지 않음
    if args.socket and args.outputfile:
        err("-w 와 -s 는 동시에 사용할 수 없습니다.")
        sys.exit(1)

    # default: 4
    pool = Pool(args.thread)

    if args.a or args.chans:
        mainLoop()
    elif args.find:
        channel_lookup(args.find.lower())

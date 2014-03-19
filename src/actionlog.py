#!/usr/bin/env python

from __future__ import print_function
import requests
import json
import time
import settings
import sys

SLEEP_SECONDS = 31


class UnexpectedResultException(Exception):
    pass


class IngressActionMonitor():
    MAX_ERRORS = 10

    def __init__(self):
        self.minTimestampMs = -1
        self.errorcount = 0

        if settings.CSRF_TOKEN == '':
            raise ValueError("Please specify valid csrf token setting")
        if settings.SESSION_ID == '':
            raise ValueError("Please specify valid session id setting")

    def write_state(self):
        f=open(settings.STATEFILE, 'w+')
        try:
            f.write(str(self.minTimestampMs))
        finally:
            f.close()
    
    def load_state(self):
        f=open(settings.STATEFILE, 'r+')
        try:
            text = f.read()
            if text:
                self.minTimestampMs = int(text)
                print('Starting at time: ', text)
        finally:
            f.close()

    def getChat(self, minTimestampMs):
        # url='http://www.ingress.com/rpc/dashboard.getPaginatedPlextsV2'
        m_apiuri = 'tmhlcb5fz9apyww2'  # GET_PAGINATED_PLEXTS
        url='https://www.ingress.com/r/' + m_apiuri

        # munge are 
        m_faction = 'codhu6b393ygyzle'  # codhu6b393ygyzle:e
        m_desiredNumItems = 'ykanusje1neibvzq'  # ykanusje1neibvzq:f
        m_maxTimestampMs = 'h2jta7ah8fn24deh'
        m_minTimestampMs = 'zblx74ndsgw9z65s'
        m_minLatE6 = '8cpt8a8ynz6dq5xn'
        m_maxLatE6 = 'js4pot11ouluvk41'
        m_minLngE6 = 'zx1x43gh5u41qa4l'
        m_maxLngE6 = 'qeb0lhwkrd641z47'

        m_apiname = 'zqjwxapf9tj3qpm6'  #  nemesis.dashboard.network.XhrController.prototype.doSendRequest_.e
        m_nazohashname = 'zmlblgphv1m7djzk'  # nemesis.dashboard.network.XhrController.prototype.doSendRequest_.e
        m_nazohashbody = '290f13d807ec19ee1a3fdd6ecdf3d7ea3e140990'
        #  m_nazotrue = 'orv7l6mjjggor28h'


        cookies = dict(csrftoken=settings.CSRF_TOKEN,
                       SACSID=settings.SESSION_ID,
                       GOOGAPPUID=797,)
        headers = {"X-CSRFToken": settings.CSRF_TOKEN,
                   "origin": r"https://www.ingress.com",
                   "Referer": r"https://www.ingress.com/intel",
                   "Content-Type": r"application/json; charset=UTF-8",
                   "User-Agent": r"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.45 Safari/537.36"}
        data = {
                m_apiname: m_apiuri,
                m_nazohashname: m_nazohashbody,
                m_faction: "all",
                m_desiredNumItems: 50,
                m_minTimestampMs: minTimestampMs,
                m_maxTimestampMs: -1,
                m_minLatE6: 34635628,
                m_maxLatE6: 36295361,
                m_minLngE6: 137530674,
                m_maxLngE6: 140947422,

                #  "1vxkm93nriulf6sf": "r26bgpb580xsf75u",  # ?means all?
                #  "2pi60k3c6ro16bar": "all",  # faction
                #  "3fdprk50o96n0dsw": "4237424919d7afaceaa09d91effe3c038fcb5681",  # ?
                #  "f3jv93vvyom5hteq": 50,  # desirednumitems

                #  "hg5rngxi8pz30yck": minTimestampMs,  # minTimestampMs
                #  "n793l18406ogclto": -1,  # maxTimestampMs

                #  "r6ygbgm4pn1vk8p2": 34635628,  # minLatE6
                #  "i556mc3zenw6wzqx": 36295361,  # maxLatE6
                #  "vo4iuf8l3wdqxobx": 137530674,  # minLngE6
                #  "w0490topwoo7bztn": 140947422,  # maxLngE6
                }

                # "desiredNumItems":50,"minLatE6":44769720,"minLngE6":-93665038,"maxLatE6":45136110,"maxLngE6":-92420150,"minTimestampMs":minTimestampMs,"maxTimestampMs":-1,"method":"dashboard.getPaginatedPlextsV2"}

        print(json.dumps(data, indent=4))
        r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
        print(r.content)

        return r.content
    
    def messagegen(self):
        jsonStr = self.getChat(self.minTimestampMs)
        responseItems = json.loads(jsonStr)
        
        if 'result' not in responseItems:
            self.errorcount += 1
            if(self.errorcount > self.MAX_ERRORS):
                print("error counter exceeded, existing...")
                sys.exit(1)

            if 'error' in responseItems:
                print(responseItems)
            else:
                raise UnexpectedResultException(jsonStr)
        else:
            responseItemsOrderedAsc = responseItems['result']
            responseItemsOrderedAsc.reverse()
            for message in responseItemsOrderedAsc:
                yield message
                self.minTimestampMs = message[1] + 1
            print(self.minTimestampMs)
    
    def actiongen(self):
        messages = self.messagegen()
        return (message for message in messages if message[2]['plext']['plextType'] == 'SYSTEM_BROADCAST')

    def monitor(self):
        self.load_state()
        while True:
            for action in self.actiongen():
                yield action
            self.write_state()
            time.sleep(SLEEP_SECONDS)

def log_lines():
    f = open(settings.LOGFILE, 'r')
    try:
        f.seek(0,2)
        while True:
            line = f.readline()
            yield line #None if no new line
    finally:
        f.close()
        
if __name__ == '__main__':
    monitor = IngressActionMonitor()
    f = open(settings.LOGFILE, 'a', 0)
    try:
        for action in monitor.monitor():
            jsonStr = json.dumps(action)
            print(jsonStr, file=f)
    finally:
        f.close()
        
    

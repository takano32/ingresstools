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
        m_apiuri = '7pscbd6vtwbibpzr'  # GET_PAGINATED_PLEXTS
        url='https://www.ingress.com/r/' + m_apiuri

        # munge are 
        m_faction = 'ah7f9puw5is6xgyz'  # nemesis.dashboard.network.PlextStore.prototype.getPlexts b.[a-z0\9]+ = c;
        m_desiredNumItems = 'gcg00bp8jz10ye3f'  # nemesis.dashboard.requests.normalizeParamCount c = {[a-z0-9]+:f,
        m_minTimestampMs = 'kjt3ck5iw2arv0o7'  # :e
        m_maxTimestampMs = 'kl23gr0z2qb2hoev'  # :f
        m_minLatE6 = 'euvaxeol6an6tbo8'  # :Math.round(d.bounds.sw.lat() * 1E6)
        m_maxLatE6 = 'gmn1na8m6d8fpudi'  # :Math.round(d.bounds.ne.lat() * 1E6)
        m_minLngE6 = '6hqe3lkjl9tt1k08'  # :Math.round(d.bounds.sw.lng() * 1E6)
        m_maxLngE6 = '5fu4jsotfjam5ue0'  # :Math.round(d.bounds.ne.lng() * 1E6)

        m_apiname = 'xrdvsoppz8khnd55'  #  nemesis.dashboard.network.XhrController.prototype.doSendRequest_  e.[a-z0-9]+ = c
        m_nazohashname = '9amimmeymgvnfrn8'  # nemesis.dashboard.network.XhrController.prototype.doSendRequest_ e["[a-z0-9]+"] =
        m_nazohashbody = '1713782d7d358b142894a0c8a605f80aa5402802'  # e["..."] = "........."
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
        
    

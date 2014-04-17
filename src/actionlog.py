#!/usr/bin/env python

from __future__ import print_function
import requests
import json
import time
import settings
import sys
import prettyprint

SLEEP_SECONDS = 31
MIN_SLEEP_SECONDS = 10
MAX_SLEEP_SECONDS = 60*3


class UnexpectedResultException(Exception):
    pass


class IngressActionMonitor():
    MAX_ERRORS = 10
    sleep_sec = SLEEP_SECONDS

    def __init__(self):
        self.minTimestampMs = -1
        self.errorcount = 0
        self.adjust_sleep()

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
        m_paginated_plexts = "34in42uj19j4yol7"  # GET_PAGINATED_PLEXTS
        url='https://www.ingress.com/r/' + m_paginated_plexts

        # munge are 
        m_chattab = "pxnxatn6f0jg6l1n"  # chattab  # nemesis.dashboard.network.PlextStore.prototype.getPlexts b.[a-z0\9]+ = c;
        m_desiredNumItems = "userolylkkbh6plw"  # nemesis.dashboard.requests.normalizeParamCount c = {[a-z0-9]+:f,
        m_maxTimestampMs = "aa17zeygsbuhev25"  # :e
        m_minTimestampMs = "ge92c4w8jjzygdey"  # :f
        m_minLatE6 = "tv2kyjpwn3hyabig"  # :Math.round(d.bounds.sw.lat() * 1E6)
        m_maxLatE6 = "0ar4f1mjmvl68uxb"  # :Math.round(d.bounds.ne.lat() * 1E6)
        m_minLngE6 = "2478kyk2vzttgylz"  # :Math.round(d.bounds.sw.lng() * 1E6)
        m_maxLngE6 = "jmfdr2j3u5gad2t8"  # :Math.round(d.bounds.ne.lng() * 1E6)

        m_method =  "5dfq4a4o4gugopfl" #  nemesis.dashboard.network.XhrController.prototype.doSendRequest_  e.[a-z0-9]+ = c
        m_version = "gwcfe0o2a6ni6g6h"  # nemesis.dashboard.network.XhrController.prototype.doSendRequest_ e["[a-z0-9]+"] = 
        m_version_parameter = "2a1be0e905823f9e342a2cd6b61f0814d0b40153"  # e["..."] = "........."  # version_parameter


        cookies = dict(csrftoken=settings.CSRF_TOKEN,
                       SACSID=settings.SESSION_ID,
                       GOOGAPPUID=797,)
        headers = {"X-CSRFToken": settings.CSRF_TOKEN,
                   "origin": r"https://www.ingress.com",
                   "Referer": r"https://www.ingress.com/intel",
                   "Content-Type": r"application/json; charset=UTF-8",
                   "User-Agent": r"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.45 Safari/537.36"}
        data = {
                m_method: m_paginated_plexts,
                m_version: m_version_parameter,
                m_chattab: "all",
                m_desiredNumItems: 50,
                m_minTimestampMs: minTimestampMs,
                m_maxTimestampMs: -1,
                m_minLatE6: 34635620,
                m_maxLatE6: 36295360,
                m_minLngE6: 137530674,
                m_maxLngE6: 140947422,
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
            self.adjust_sleep(0)
            if(self.errorcount > self.MAX_ERRORS):
                print("error counter exceeded, existing...")
                sys.exit(1)

            if 'error' in responseItems:
                print(responseItems)
            else:
                raise UnexpectedResultException(jsonStr)
        else:
            self.errorcount = 0
            responseItemsOrderedAsc = responseItems['result']
            responseItemsOrderedAsc.reverse()
            for message in responseItemsOrderedAsc:
                yield message
                self.minTimestampMs = message[1] + 1
            prettyprint.pp(responseItems)

            print(self.minTimestampMs)
            tm = time.localtime(self.minTimestampMs/1000.0)
            print("%04d/%02d/%02d %02d:%02d:%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec))

            counts = len(responseItemsOrderedAsc)
            self.adjust_sleep(counts)

            print("counts: %d" % len(responseItemsOrderedAsc))
            print("sleep_sec: %d" % self.sleep_sec)
    

    def adjust_sleep(self, factor=None):
        """ factor: count of messages per unit time """
        if factor is None:
            self.sleep_sec = SLEEP_SECONDS

        else:
            if factor != 0:
                self.sleep_sec = MAX_SLEEP_SECONDS/factor + MIN_SLEEP_SECONDS
            else:
                self.sleep_sec = MAX_SLEEP_SECONDS+MIN_SLEEP_SECONDS

            if self.sleep_sec > (MAX_SLEEP_SECONDS+MIN_SLEEP_SECONDS):
                self.sleep_sec = (MAX_SLEEP_SECONDS+MIN_SLEEP_SECONDS)
            elif self.sleep_sec < MIN_SLEEP_SECONDS:
                self.sleep_sec = MIN_SLEEP_SECONDS


    def actiongen(self):
        messages = self.messagegen()
        return (message for message in messages if message[2]['plext']['plextType'] == 'SYSTEM_BROADCAST')

    def monitor(self):
        self.load_state()
        while True:
            for action in self.actiongen():
                yield action
            self.write_state()
            time.sleep(self.sleep_sec)


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
        
    

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
        m_paginated_plexts = "nmhxd48xgv27smx5"  # GET_PAGINATED_PLEXTS
        url='https://www.ingress.com/r/' + m_paginated_plexts

        # munge are 
        m_chattab = "8yimcev6se2rmoj5"  # chattab  # nemesis.dashboard.network.PlextStore.prototype.getPlexts b.[a-z0\9]+ = c;
        m_desiredNumItems = "rsye6nmi5dzpg3gr"  # nemesis.dashboard.requests.normalizeParamCount c = {[a-z0-9]+:f,
        m_maxTimestampMs = "ieymvz2sicy4os3e"  # :e
        m_minTimestampMs = "wvtqwehkckfqil8j"  # :f
        m_minLatE6 = "oms6l6yxils4j65y"  # :Math.round(d.bounds.sw.lat() * 1E6)
        m_maxLatE6 = "emplv6y80d7fgerd"  # :Math.round(d.bounds.ne.lat() * 1E6)
        m_minLngE6 = "h93t7tti5fajkxl0"  # :Math.round(d.bounds.sw.lng() * 1E6)
        m_maxLngE6 = "o3c2s79aoopfw4bq"  # :Math.round(d.bounds.ne.lng() * 1E6)

        m_method =  "pkxmjvp7xm2r3kny" #  nemesis.dashboard.network.XhrController.prototype.doSendRequest_  e.[a-z0-9]+ = c
        m_version = "48s4o2iz9kquduj5"  # nemesis.dashboard.network.XhrController.prototype.doSendRequest_ e["[a-z0-9]+"] = 
        m_version_parameter = "9dcc12279cbd2c890d1eb48f398eaf06947d8b6f"  # e["..."] = "........."  # version_parameter


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
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
            print(r.content)

        except:
            r.content = None

        return r.content
    

    def messagegen(self):
        jsonStr = self.getChat(self.minTimestampMs)
        responseItems = []
        try:
            responseItems = json.loads(jsonStr)

        except ValueError:
            pass
        
        if 'result' not in responseItems:
            self.errorcount += 1
            self.adjust_sleep(0)
            if(self.errorcount > self.MAX_ERRORS):
                print("error counter exceeded, existing...")
                raise UnexpectedResultException(jsonStr)
                # sys.exit(1)

            if 'error' in responseItems:
                print(responseItems)
            else:
                self.errorcount += 1
        else:
            self.errorcount = 0
            responseItemsOrderedAsc = responseItems['result']
            responseItemsOrderedAsc.reverse()
            for message in responseItemsOrderedAsc:
                yield message
                self.minTimestampMs = message[1] + 1
            prettyprint.pp(responseItems)

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
        
    

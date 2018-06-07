#-------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# Copyright 2017 Cognizant Technology Solutions
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
#-------------------------------------------------------------------------------
'''
Created on Jul 6, 2017

@author: 463188
'''
# Optimization and Pagination might be required. This is the first cut working agent with incremental fetch

from dateutil import parser
from com.cognizant.devops.platformagents.core.BaseAgent import BaseAgent
from urllib import quote
import time
import json,ast

class RallyRun(BaseAgent):
    def process(self):
        userid = self.config.get("userid", '')
        passwd = self.config.get("passwd", '')
        baseUrl = self.config.get("baseUrl", '')
        iteration = self.config.get("warriors", '')
        incredible = self.config.get("incredibles", '')
        eagle = self.config.get("eagles", '')
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        responseTemplate = self.getResponseTemplate()
        proj = [iteration,incredible,eagle]
        for hierarchy in proj:
            Iter = self.getResponse(hierarchy, 'GET', userid, passwd, None)
            data = []
            for url in Iter["QueryResult"]["Results"]:
                sdate = url['StartDate']
                sdate = parser.parse(sdate)
                sdate = sdate.strftime('%Y-%m-%d')
                edate = url['EndDate']
                edate = parser.parse(edate)
                edate = edate.strftime('%Y-%m-%d')
                set = url['WorkProducts']['_ref']
                itername = url['Name']
                set = set+"?pagesize=2000"
                response = self.getResponse(set, 'GET', userid, passwd, None)
                if len(response)>0:
                    for text in response["QueryResult"]["Results"]:
                        if text['TestCases']:
                            testcount = text['TestCases']['Count']
                            test = text['TestCases']['_ref']
                            test = test+"?pagesize=2000"
                            testres = self.getResponse(test, 'GET', userid, passwd, None)
                            if len(testres)>0:
                                for res in testres["QueryResult"]["Results"]:
                                    data = []
                                    injectData = {}
                                    name = res['FormattedID']
                                    since = self.tracking.get(name,None)
                                    if since == None:
                                        lastUpdated = startFrom
                                    else:
                                        since = parser.parse(since)
                                        since = since.strftime('%Y-%m-%d')
                                        lastUpdated = since
                                    if res['LastUpdateDate'] != None:
                                        date = res['LastUpdateDate']
                                    else:
                                        date = res['CreationDate']
                                    date = parser.parse(date)
                                    date = date.strftime('%Y-%m-%d')
                                    if since == None or date > since:
                                        if res['LastUpdateDate'] != None:
                                            injectData['lastUpdateDate'] = res['LastUpdateDate']
                                        else:
                                            injectData['lastUpdateDate'] = res['CreationDate']
                                        injectData['id'] = res['FormattedID']
                                        injectData['testCaseCount'] = testcount
                                        injectData['lastRun'] = res['LastRun']
                                        if res['LastVerdict']:
                                            injectData['lastVerdict'] = res['LastVerdict']
                                        else:
                                            injectData['lastVerdict'] = "null"
                                        injectData['iteration'] = itername
                                        injectData['startDate'] = sdate
                                        injectData['endDate'] = edate
                                        injectData['Project'] = res['Project']['_refObjectName']
                                        data.append(injectData)
                                        seq = [x['lastUpdateDate'] for x in data]
                                        fromDateTime = max(seq)
                                        fromDateTime = parser.parse(fromDateTime)
                                        fromDateTime = fromDateTime.strftime('%Y-%m-%d')
                                    else:
                                        fromDateTime = lastUpdated
                                    if len(testres)>0:
                                        self.tracking[name] = fromDateTime
                                        self.publishToolsData(data)
                                        self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    RallyRun()

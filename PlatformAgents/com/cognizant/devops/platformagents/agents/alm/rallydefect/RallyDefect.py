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

class RallyDefect(BaseAgent):
    def process(self):
        userid = self.config.get("userid", '')
        passwd = self.config.get("passwd", '')
        baseUrl = self.config.get("baseUrl", '')
        releaseurl = self.config.get("WarriorsRelease", '')
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        responseTemplate = self.getResponseTemplate()
        release = self.getResponse(releaseurl, 'GET', userid, passwd, None)
        for url in release["QueryResult"]["Results"]:
            data = []
            relname = str(url['_refObjectName'])
            name="\""+quote(relname)+"\""
            since = self.tracking.get(relname,None)
            if since == None:
                lastUpdated = startFrom
            else:
                since = parser.parse(since)
                since = since.strftime('%Y-%m-%d')
                lastUpdated = since
            urlappend_release_name="Release.Name = "+name
            releaseName=urlappend_release_name
            #url = "https://rally1.rallydev.com/slm/webservice/v2.0/workspace/13785475169"+"&query=("+releaseName+")"
            hierachiesUrl = baseUrl+"defect?query=("+releaseName+")&pagesize=30&query=(LastUpdateDate>"+lastUpdated+")"
            hierachies = self.getResponse(hierachiesUrl, 'GET', userid, passwd, None)
            for hierarchy in hierachies["QueryResult"]["Results"]:
                injectData = {}
                reference = hierarchy['_ref']
                ref = self.getResponse(reference, 'GET', userid, passwd, None)
               # inject data is used as sample here update with actual values needed if any
                date = ref['Defect']['LastUpdateDate']
                date = parser.parse(date)
                date = date.strftime('%Y-%m-%d')
                if since == None or date > since:
                    injectData['Status'] = ref['Defect']['State']
                    # injectData['Defect'] = "Defect"
                    Closed = ref['Defect']['ClosedDate']
                    if Closed is not None:
                        Closed = parser.parse(Closed)
                        Closed = Closed.strftime('%Y-%m-%d')
                        injectData['ClosedDate'] = Closed
                    else:
                        injectData['ClosedDate'] = Closed
                    injectData['ID'] = ref['Defect']['FormattedID']
                    if ref['Defect']['Iteration']:
                        injectData['Iteration'] = ref['Defect']['Iteration']['_refObjectName']
                    injectData['Release'] = relname
                    injectData['Environment'] = ref['Defect']['Environment']
                    check = ref['Defect']['CreationDate']
                    if check is not None:
                        check = parser.parse(check)
                        check = check.strftime('%Y-%m-%d')
                        injectData['OpenedDate'] = check
                    else:
                        injectData['OpenedDate'] = check
                    Update = ref['Defect']['LastUpdateDate']
                    Update = parser.parse(Update)
                    Update = Update.strftime('%Y-%m-%d')
                    injectData['LastUpdateDate'] = Update
                    injectData['Project'] = ref['Defect']['Project']['_refObjectName']
                    data += self.parseResponse(responseTemplate, hierarchy, injectData)
                    seq = [x['LastUpdateDate'] for x in data]
                    fromDateTime = max(seq)
                    fromDateTime = parser.parse(fromDateTime)
                    fromDateTime = fromDateTime.strftime('%d/%m/%Y')
                else:
                    fromDateTime = lastUpdated
            if len(hierachies)>0:
                self.tracking[relname] = fromDateTime
                self.publishToolsData(data)
                self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    RallyDefect()

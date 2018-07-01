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
import string
import json
import requests
from requests.auth import HTTPBasicAuth

class RallyTag(BaseAgent):
    def process(self):
        baseUrl = self.config.get("baseUrl", '')
        token = self.config.get("token", '')
        sst = self.config.get("SST", '')
        dtams = self.config.get("DTAMS", '')
        fz = self.config.get("FZ", '')
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        responseTemplate = self.getResponseTemplate()
        tag = [sst,dtams,fz]
        for response in tag:
            tag = "\""+quote(response)+"\""
            url = baseUrl+"?types=hierarchicalrequirement,defect,defectsuite,testset&pagesize=20&query=(Tags CONTAINS "+tag+")&fetch=Release,DisplayColor,Project,ObjectID,Name,Tags,DragAndDropRank,FormattedID,ScheduleState,Blocked,Ready,ScheduleStatePrefix,Iteration,Owner,LastUpdateDate,VersionId&includePermissions=true&compact=true&workspace=/workspace/13785475169"
            data = []
            hierachies = requests.get(url, auth=(token, ''), verify=False)
            hierachies = json.loads(hierachies.text)
            for hierarchy in hierachies["QueryResult"]["Results"]:
                injectData = {}
                data = []
                date = hierarchy['LastUpdateDate']
                date = parser.parse(date)
                date = date.strftime('%Y-%m-%dT%H:%M:%S')
                userstory =  hierarchy['FormattedID']
                injectData['userStory']=hierarchy['FormattedID']
                injectData['scheduleState']=hierarchy['ScheduleState']
                injectData['lastUpdate']=hierarchy['LastUpdateDate']
                if 'Name' in hierarchy['Project']:
                    injectData['Project']=hierarchy['Project']['Name']
                if 'Name' in hierarchy['Release']:
                    injectData['Release']=hierarchy['Release']['Name']
                if 'Name' in hierarchy['Iteration']:
                    injectData['Iteration']=hierarchy['Iteration']['Name']
                length = len(hierarchy['Tags']['_tagsNameArray'])-1
                if length == 0:
                    val=hierarchy['Tags']['_tagsNameArray'][0]['Name']
                    string=val.split(" ")
                    val=string[0]
                    injectData[val]=hierarchy['Tags']['_tagsNameArray'][0]['Name']
                else:
                    for i in range(0,length):
                        val=hierarchy['Tags']['_tagsNameArray'][i]['Name']
                        string=val.split(" ")
                        val=string[0]
                        injectData[val]=hierarchy['Tags']['_tagsNameArray'][i]['Name']
                data.append(injectData)
                date = hierarchy['LastUpdateDate']
                fromDateTime = date
                if data!=[]:
                    self.tracking[userstory] = fromDateTime
                    self.publishToolsData(data)
                    self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    RallyTag()

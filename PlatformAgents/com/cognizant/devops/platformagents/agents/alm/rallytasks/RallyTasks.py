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
import json
import requests
from requests.auth import HTTPBasicAuth


class RallyTasks(BaseAgent):
    def process(self):
        token = self.config.get("token", '')
        baseUrl = self.config.get("baseUrl", '')
        warriors = self.config.get("WarriorsRelease", '')
        incredibles = self.config.get("incredibles", '')
        eagles = self.config.get("eagles", '')
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        responseTemplate = self.getResponseTemplate()
        proj = [warriors,incredibles,eagles]
        for projects in proj:
            release = requests.get(projects, auth=(token, ''), verify=False)
            release = json.loads(release.text)
            data = []
            for url in release["QueryResult"]["Results"]:
                relname = str(url['_refObjectName'])
                name="\""+quote(relname)+"\""
                project = str(url['Project']['_refObjectName'])
                since = self.tracking.get(relname,None)
                if since == None:
                    lastUpdated = startFrom
                else:
                    since = parser.parse(since)
                    since = since.strftime('%Y-%m-%dT%H:%M:%S')
                    lastUpdated = since
                urlappend_release_name="Release.Name = "+name
                releaseName=urlappend_release_name
                data = []
                url = "https://rally1.rallydev.com/slm/webservice/v2.0/workspace/13785475169"+"&query=("+releaseName+")"
                hierachiesUrl = baseUrl+"hierarchicalrequirement?workspace="+url+"&query=(LastUpdateDate>"+lastUpdated+")"+"&pagesize=2000"
                hierachies = requests.get(hierachiesUrl, auth=(token, ''), verify=False)
                hierachies = json.loads(hierachies.text)
                for hierarchy in hierachies["QueryResult"]["Results"]:
                    injectData = {}
                    reference = hierarchy['_ref']
                    ref = requests.get(reference, auth=(token, ''), verify=False)
                    ref = json.loads(ref.text)
                    if ref['HierarchicalRequirement']['Iteration']:
                        iteration = ref['HierarchicalRequirement']['Iteration']['_ref']
                        iteration = iteration+"?pagesize=2000"
                        iter = requests.get(iteration, auth=(token, ''), verify=False)
                        iter = json.loads(iter.text)
                        date = ref['HierarchicalRequirement']['LastUpdateDate']
                        date = parser.parse(date)
                        date = date.strftime('%Y-%m-%dT%H:%M:%S')
                        if since == None or date > since:
                            injectData['LastUpdateDate'] = ref['HierarchicalRequirement']['LastUpdateDate']
                            injectData['ReleaseName'] = relname
                            injectData['userStory'] = ref['HierarchicalRequirement']['FormattedID']
                            injectData['defects'] = ref['HierarchicalRequirement']['Defects']['Count']
                            injectData['iteration'] = iter['Iteration']['Name']
                            injectData['planEstimatePoints'] = ref['HierarchicalRequirement']['PlanEstimate']
                            injectData['sprintStartDate'] = iter['Iteration']['StartDate']
                            injectData['scheduleState'] = ref['HierarchicalRequirement']['ScheduleState']
                            injectData['sprintEndDate'] = iter['Iteration']['EndDate']
                            injectData['Project'] = project
                            injectData['taskRemainingTotal'] = ref['HierarchicalRequirement']['TaskRemainingTotal']
                            injectData['taskEstimateTotal'] = ref['HierarchicalRequirement']['TaskEstimateTotal']
                            injectData['taskActualTotal'] = ref['HierarchicalRequirement']['TaskActualTotal']
                            injectData['passingTestcase'] = ref['HierarchicalRequirement']['PassingTestCaseCount']
                            injectData['TotalTasks'] = ref['HierarchicalRequirement']['Tasks']['Count']
                            injectData['TotalTestCase'] = ref['HierarchicalRequirement']['TestCaseCount']
                            injectData['Taskstatus'] = ref['HierarchicalRequirement']['TaskStatus']
                            ChangedDate = ref['HierarchicalRequirement']['FlowStateChangedDate']
                            ChangedDate = parser.parse(ChangedDate)
                            ChangedDate = ChangedDate.strftime('%Y-%m-%d')
                            injectData['FlowStateChangedDate'] = ChangedDate
                            data.append(injectData)
                            seq = [x['LastUpdateDate'] for x in data]
                            fromDateTime = max(seq)
                            fromDateTime = parser.parse(fromDateTime)
                            fromDateTime = fromDateTime.strftime('%Y-%m-%dT%H:%M:%S')
                        else:
                            fromDateTime = lastUpdated
                        if len(hierachies)>0:
                            self.tracking[relname] = fromDateTime
                            self.publishToolsData(data)
                            self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    RallyTasks()

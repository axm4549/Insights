#-------------------------------------------------------------------------------
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
Created on Jul 1, 2016

@author: 463188
'''
from dateutil import parser
from datetime import datetime
from datetime import timedelta
import json
import requests
from requests.auth import HTTPBasicAuth
from com.cognizant.devops.platformagents.core.BaseAgent import BaseAgent

class SonarAgent(BaseAgent):
    def process(self):
        baseUrl = self.config.get("baseUrl", '')
        projectsUrl = baseUrl+"api/projects/index?format=json&pagesize=2000"
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        timeStampFormat = self.config.get('timeStampFormat')
        startFrom = startFrom.strftime(timeStampFormat)
        userId = self.config.get("UserId", '')
        password = self.config.get("Password", '')
        token = self.config.get("token", '')
        timeMachineapi = self.config.get("timeMachineapi", '')
        #sonarProjects = self.getResponse(projectsUrl, 'GET', token, None)
        sonarProjects = requests.get(projectsUrl, auth=(token, ''), verify=False)
        sonarProjects = json.loads(sonarProjects.text)
        metrics = self.config.get('dynamicTemplate', {}).get("metrics", '')
        metricsParam = ''
        if len(metrics) > 0:
            for metric in metrics:
                metricsParam += metric + ','
        data = []
        for project in sonarProjects:
            data = []
            projectKey = project["k"]
            projectName = project["nm"]
            timestamp = self.tracking.get(projectKey, startFrom)
            if timeMachineapi == "yes":
                sonarExecutionsUrl = baseUrl+"api/timemachine/index?metrics="+metricsParam+"&resource="+projectKey+"&fromDateTime="+timestamp+"&format=json"
            else:
                timestamp=timestamp.replace("+","%2B")
                sonarExecutionsUrl = baseUrl+"api/measures/search_history?metrics="+metricsParam+"&component="+projectKey+"&from="+timestamp+"&format=json"
            #sonarExecutions = self.getResponse(sonarExecutionsUrl, 'GET', token, None)
            sonarExecutions = requests.get(sonarExecutionsUrl, auth=(token, ''), verify=False)
            sonarExecutions = json.loads(sonarExecutions.text)
            lastUpdatedDate = None
            if timeMachineapi =="yes":
                for sonarExecution in sonarExecutions:
                    metricsColumns = []
                    cols = sonarExecution['cols']
                    for col in cols:
                        metricsColumns.append(col['metric'])
                    cells = sonarExecution['cells']
                    for cell in cells:
                        executionData = {}
                        executionData['metricdate'] = cell['d']
                        executionData["resourcekey"] = projectKey
                        executionData["projectName"] = projectName
                        metricValues = cell['v']
                        for i in range(len(metricValues)):
                            executionData[metricsColumns[i]] = metricValues[i]
                        data.append(executionData)
                        lastUpdatedDate = executionData['metricdate']
            else:
                var = len(sonarExecutions['measures'][0]['history'])-1
    #            for historydata in var:
                executionData={}
                for i_metric_length in range(0,len(sonarExecutions['measures'])):
                    if 'value' in sonarExecutions['measures'][i_metric_length]['history'][var]:
                        executionData['resourcekey']=projectKey
                        executionData["projectName"] = projectName
                        executionData['metricdate']=sonarExecutions['measures'][i_metric_length]['history'][var]['date']
                        executionData[sonarExecutions['measures'][i_metric_length]['metric']]=sonarExecutions['measures'][i_metric_length]['history'][var]['value']
                        lastUpdatedDate = executionData['metricdate']
            data.append(executionData)
                    #lastUpdatedDate = executionData['metricdate']
            if lastUpdatedDate:
                lastUpdatedDate = lastUpdatedDate[:self.dateTimeLength]
                dt = datetime.strptime(lastUpdatedDate, timeStampFormat)
                fromDateTime = dt + timedelta(seconds=01)
                fromDateTime = fromDateTime.strftime(timeStampFormat)
                self.tracking[projectKey] = fromDateTime
                self.publishToolsData(data)
                self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    SonarAgent()

from dateutil import parser
from com.cognizant.devops.platformagents.core.BaseAgent import BaseAgent
from urllib import quote
import time
import json
import requests
from requests.auth import HTTPBasicAuth

class RallyDefect(BaseAgent):
    def process(self):
        baseUrl = self.config.get("baseUrl", '')
        token = self.config.get("token", '')
        Warriors = self.config.get("WarriorsRelease", '')
        incredibles = self.config.get("incredibles", '')
        Eagles = self.config.get("EaglesRelease", '')
        startFrom = self.config.get("startFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        responseTemplate = self.getResponseTemplate()
        project = [Warriors,incredibles,Eagles]
        for link in project:
            release = requests.get(link, auth=(token, ''), verify=False)
            release = json.loads(release.text)
            for url in release["QueryResult"]["Results"]:
                data = []
                relname = str(url['_refObjectName'])
                name="\""+quote(relname)+"\""
                since = self.tracking.get(relname,None)
                if since == None:
                    lastUpdated = startFrom
                else:
                    since = parser.parse(since)
                    since = since.strftime('%Y-%m-%dT%H:%M:%S')
                    lastUpdated = since
                urlappend_release_name="Release.Name = "+name
                releaseName=urlappend_release_name
                hierachiesUrl = baseUrl+"defect?query=("+releaseName+")&pagesize=2000&query=(LastUpdateDate>"+lastUpdated+")"
                hierachies = requests.get(hierachiesUrl, auth=(token, ''), verify=False)
                hierachies = json.loads(hierachies.text)
                if len(hierachies["QueryResult"]["Results"]) != 0:
                    for hierarchy in hierachies["QueryResult"]["Results"]:
                        injectData = {}
                        reference = hierarchy['_ref']
                        reference = reference+"?pagesize=2000"
                        ref = requests.get(reference, auth=(token, ''), verify=False)
                        ref = json.loads(ref.text)
                   # inject data is used as sample here update with actual values needed if any
                        date = ref['Defect']['LastUpdateDate']
                        date = parser.parse(date)
                        date = date.strftime('%Y-%m-%dT%H:%M:%S')
                        if since == None or date > since:
                            injectData['Status'] = ref['Defect']['State']
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
                            injectData['LastUpdateDate'] = ref['Defect']['LastUpdateDate']
                            injectData['Project'] = ref['Defect']['Project']['_refObjectName']
                            data.append(injectData)
                            seq = [x['LastUpdateDate'] for x in data]
                            fromDateTime = max(seq)
                            fromDateTime = parser.parse(fromDateTime)
                            fromDateTime = fromDateTime.strftime('%Y-%m-%dT%H:%M:%S')
                        else:
                            fromDateTime = lastUpdated
                    if data!=[]:
                        self.tracking[relname] = fromDateTime
                        self.publishToolsData(data)
                        self.updateTrackingJson(self.tracking)
                else:
                    continue
if __name__ == "__main__":
    RallyDefect()

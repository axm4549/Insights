from __future__ import unicode_literals
import boto3
from com.cognizant.devops.platformagents.core.BaseAgent import BaseAgent
from urllib import quote
import time
from dateutil import parser
import json, ast

class AwsCodePipeline(BaseAgent):
    def process(self):
        startFrom = self.config.get("StartFrom", '')
        startFrom = parser.parse(startFrom)
        startFrom = startFrom.strftime('%Y-%m-%dT%H:%M:%S')
        client = boto3.client('codepipeline')
        response = client.list_pipelines()
        length = len(response['pipelines'])
        pipeline = []
        for n in range(0,length):
            res = str(response['pipelines'][n]['name'])
            pipeline.append(res)
        pipeline=list(set(pipeline))
        for value in pipeline:
            response = client.list_pipeline_executions(
                 pipelineName=value
                 )
            injectData = {}
            tracking_data = []
            since = self.tracking.get(value,None)
            if since == None:
                lastUpdated = startFrom
            else:
                since = parser.parse(since)
                since = since.strftime('%Y-%m-%dT%H:%M:%S')
                pattern = '%Y-%m-%dT%H:%M:%S'
                since = int(time.mktime(time.strptime(since,pattern)))
                lastUpdated = since
            date = str(response['pipelineExecutionSummaries'][0]['lastUpdateTime'])
            date = parser.parse(date)
            date = date.strftime('%Y-%m-%dT%H:%M:%S')
            pattern = '%Y-%m-%dT%H:%M:%S'
            date = int(time.mktime(time.strptime(date,pattern)))
            if since == None or date > since:
               for response in response['pipelineExecutionSummaries']:
                   injectData['pipelineName'] = value
                   injectData['status'] = str(response['status'])
                   injectData['jobId'] = str(response['pipelineExecutionId'])
                   injectData['createTime'] = str(response['startTime'])
                   start = str(response['startTime'])
                   start = parser.parse(start)
                   start_e = start.strftime('%Y-%m-%dT%H:%M:%S')
                   start_f = start.strftime('%Y-%m-%d')
                   injectData['startTime'] = start_f
                   pattern = '%Y-%m-%dT%H:%M:%S'
                   epoch = int(time.mktime(time.strptime(start_e,pattern)))
                   injectData['startTimeepoch'] = epoch
                   date = str(response['lastUpdateTime'])
                   date = parser.parse(date)
                   date = date.strftime('%Y-%m-%dT%H:%M:%S')
                   injectData['lastUpdateTime'] = date
                   pattern = '%Y-%m-%dT%H:%M:%S'
                   date = int(time.mktime(time.strptime(date,pattern)))
                   injectData['lastUpdateTimeepoch'] = date
                   string = ast.literal_eval(json.dumps(injectData))
                   tracking_data.append(string)
                   seq = [x['lastUpdateTime'] for x in tracking_data]
                   fromDateTime = max(seq)
            else:
               fromDateTime = lastUpdated
            self.tracking[value] = fromDateTime
            if tracking_data!=[]:
                self.publishToolsData(tracking_data)
                self.updateTrackingJson(self.tracking)
if __name__ == "__main__":
    AwsCodePipeline()

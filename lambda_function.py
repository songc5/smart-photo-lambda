import json
import boto3
import uuid
import requests
from requests_aws4auth import AWS4Auth
import base64



def send_to_lex(query, userId):
    # send query message to lex, get response and extract slots
    lex = boto3.client('lex-runtime')
    response = lex.post_text(
        botName='lexbot',
        botAlias='lexbot',
        userId=str(userId),
        sessionAttributes={
            #'string': 'string'
        },
        inputText=query
        )
    # print(response)
    keys = [x for x in response['slots'].values() if x]
    # print(keys)
    return keys


def elastic_search(labels):
    # to do: return list of image names
    region = 'us-east-1' # For example, us-west-1
    service = 'es'
    awsauth = AWS4Auth('', '', region, service)
    host = 'https://search-photos-fryaeg5aafmsirrempdlfkmz4a.us-east-1.es.amazonaws.com' 
    index = 'photos'
    url = host + '/' + index + '/_search'
    headers = { "Content-Type": "application/json" }
    res = []
    for l in labels:
        query = {
        "size": 100,
        "query": {
            "multi_match": {
                "query":    l, 
                }
            }
        }
        r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
        data = json.loads(r.text)['hits']['hits']
        res.append(data)
    # print("data is")
    # print(data)
    names = get_names(res)
    return list(names)

def get_names(response):
    names = []
    for label_response in response:
        for label in label_response:
            name = label["_source"]["objectKey"]
            names.append(name)
    return set(names)

def get_photos_from_s3(photos):
    binary_photos = []
    s3 = boto3.client('s3')
    for p in photos:
        fileObj = s3.get_object(Bucket = 'photosbucket112', Key = p)
        file_content = fileObj['Body'].read()
        binary_photos.append(base64.b64encode(file_content))
        # binary_photos.append(file_content)
    return binary_photos
def lambda_handler(event, context):
   
    # event={'body-json': {}, 'params': {'path': {'bucket': 'photosbucket112'}, 'querystring': {'query_text': 'show me moon'}, 'header': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Host': '2f2oruw7m3.execute-api.us-east-1.amazonaws.com', 'Postman-Token': '1da32d66-4566-40c0-b13c-e39cdbe2f85e', 'User-Agent': 'PostmanRuntime/7.28.4', 'x-amz-meta-customLabels': 'm1,m3', 'X-Amzn-Trace-Id': 'Root=1-61875336-433dad25722a06f74861abbd', 'X-Forwarded-For': '198.254.113.88', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': '2f2oruw7m3', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'GET', 'stage': 'dev', 'source-ip': '198.254.113.88', 'user': '', 'user-agent': 'PostmanRuntime/7.28.4', 'user-arn': '', 'request-id': '37d7937a-4b75-407c-9d9c-09bd4db8f1d2', 'resource-id': 'xqq0m4', 'resource-path': '/{bucket}'}}

    query = event['params']['querystring']['query_text']
    # print(query)
    userId = str(uuid.uuid1())
    labels = send_to_lex(query, userId)
    photo_names = elastic_search(labels)
    print(photo_names)
    print('__________________________')
    res = get_photos_from_s3(photo_names)
    return res

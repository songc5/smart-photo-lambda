import json
import boto3
import datetime
import requests
from requests_aws4auth import AWS4Auth

def getS3key(event):
    image_name = event['Records'][0]['s3']['object']['key']
    print(image_name)
    res = {
        'S3Object': {
            'Bucket': 'photosbucket112',
            'Name': image_name
            }
        }
    return image_name
    
    
def get_time(event):
    time = event['Records'][0]['eventTime']
    return time

def get_labels(client, image_name):
    in_put = {
        'S3Object': {
            'Bucket': 'photosbucket112',
            'Name': image_name
            }
        }
    response = client.detect_labels(Image = in_put, MinConfidence = 90)
    labels = [x["Name"] for x in response["Labels"]]
    return labels

def get_head(client, image_name):
    response = client.head_object(Bucket='photosbucket112', Key=image_name)
    print(response)
    # print(response)
    customLabels = None
    if len(response["Metadata"]) != 0:
        customLabels = response["Metadata"]['customlabels'].split(',')
    # createdTime = response["LastModified"].strftime("%Y-%m-%%dT%H:%M:%S")
    return customLabels
    
    
def get_json_formate(key, time, lables):
    res = {
            'objectKey': key,
            'bucket': 'photosbucket112',
            'createdTimestamp': time,
            'labels': lables
        }
    # json_string = json.dumps(res)
    return res


def send_to_elastic(value):
    region = 'us-east-1'
    service = 'es'
    # credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth('', '', region, service)
    host = 'https://search-photos-fryaeg5aafmsirrempdlfkmz4a.us-east-1.es.amazonaws.com'
    index = 'photos'
    type = '_doc'
    url = host + '/' + index + '/' + type
    headers = { "Content-Type": "application/json" }
    r = requests.post(url, auth=awsauth, json=value, headers=headers)
    return r.text
    

def lambda_handler(event, context):
    print(event)
    image = getS3key(event)
    created_time = get_time(event)
    client = boto3.client("rekognition")
    raw_labels = get_labels(client, image)
    client2 = boto3.client("s3")
    custom_labels = get_head(client2, image)
    
    labels = raw_labels
    if custom_labels:
        labels = raw_labels+custom_labels
    
    # TODO implement
    print('triggered')
    print(labels)
    store_json = get_json_formate(image, created_time, labels)
    print('______________')
    print(store_json)
    
    #send json to elastic search
    tp = send_to_elastic(store_json)
    print(tp)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def test():
    client2 = boto3.client("s3")
    time, res = get_head(client2, 'img2.png')
    print(res)
    print(time)

def test2():
    client = boto3.client("rekognition")
    raw_labels = get_labels(client, 'img2.png')
    print(raw_labels)
    

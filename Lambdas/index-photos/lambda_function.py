import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    # Initialize AWS services clients
    s3_client = boto3.client('s3')
    rekognition_client = boto3.client('rekognition')

    # Constants (typically set as environment variables)
    region = 'us-east-1'  # Hardcoded region
    es_host = 'search-photos-g3me562ui3g7a4ucz2nongmdaa.us-east-1.es.amazonaws.com'  # Hardcoded Elasticsearch endpoint

    # AWS authentication setup
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

    # Extract S3 bucket name and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(f"Processing file: {key} from bucket: {bucket}")

    # Fetch the image from S3
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        print("Image successfully retrieved from S3.")
    except Exception as e:
        print(f"Failed to retrieve image from S3: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps("Failed to retrieve image from S3")}

    # Use AWS Rekognition to detect labels in the image
    try:
        rekognition_response = rekognition_client.detect_labels(
            Image={'Bytes': image_data},
            MaxLabels=10
        )
        labels = [label['Name'] for label in rekognition_response['Labels']]
        print(f"Labels detected: {labels}")
    except Exception as e:
        print(f"Failed to detect labels with Rekognition: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps("Failed to detect labels")}

    # Prepare data to index in Elasticsearch
    index_data = {
        'objectKey': key,
        'bucket': bucket,
        'createdTimestamp': event['Records'][0]['eventTime'],
        'labels': labels
    }
    print(f"Indexing the following data to Elasticsearch: {json.dumps(index_data)}")

    # Elasticsearch index operation URL
    url = f"https://{es_host}/photos/_doc"

    # Send data to Elasticsearch using the requests library
    headers = {"Content-Type": "application/json"}
    es_response = requests.post(url, auth=awsauth, json=index_data, headers=headers)

    # Check response from Elasticsearch
    if es_response.status_code == 201:
        print("Successfully indexed image in Elasticsearch.")
        response_body = f"Successfully indexed image in Elasticsearch! Response: {es_response.text}"
    else:
        print(f"Error sending data to Elasticsearch: {es_response.text}")
        response_body = f"Failed to index image. Elasticsearch response: {es_response.text}"

    return {
        'statusCode': es_response.status_code,
        'body': json.dumps(response_body)
    }

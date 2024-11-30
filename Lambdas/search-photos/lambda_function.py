import json
import boto3
from requests_aws4auth import AWS4Auth
import requests

def lambda_handler(event, context):
    # Extract the query string from the API Gateway event
    query = event.get('queryStringParameters', {}).get('q', '')

    if not query:
        print("No query provided.")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'No query provided'})
        }

    print(f"Received query: {query}")

    # Set up AWS credentials for accessing Elasticsearch
    region = 'us-east-1'  # Use the region where your Elasticsearch domain is hosted
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    # Elasticsearch host and endpoint
    es_host = 'search-photos-g3me562ui3g7a4ucz2nongmdaa.us-east-1.es.amazonaws.com'
    url = f'https://{es_host}/photos/_search'

    # Elasticsearch query
    search_query = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["labels"]
            }
        }
    }

    headers = {'Content-Type': 'application/json'}
    try:
        print(f"Constructed Elasticsearch query: {json.dumps(search_query)}")
        response = requests.get(url, auth=awsauth, headers=headers, json=search_query)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error querying Elasticsearch: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Failed to perform the search due to a server error.'})
        }

    # Parse response from Elasticsearch
    if response.status_code == 200:
        hits = response.json()['hits']['hits']
        if hits:
            print(f"Search successful. Found {len(hits)} results.")
            bucket_name = "your-photo-bucket-adrian"  # Replace with your S3 bucket name
            base_url = f"https://{bucket_name}.s3.amazonaws.com/"
            results = []

            for hit in hits:
                source = hit['_source']
                image_key = source.get('objectKey', '')  # S3 object key
                labels = source.get('labels', [])
                if image_key:  # Ensure there's a valid object key
                    results.append({
                        "url": f"{base_url}{image_key}",
                        "labels": labels
                    })

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'results': results})
            }
        else:
            print("No results found.")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'results': []})
            }
    else:
        print(f"Error querying Elasticsearch: {response.text}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Failed to perform the search due to a server error.'})
        }

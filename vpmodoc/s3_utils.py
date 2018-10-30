import boto3
import os
from django.conf import settings

def generate_s3_client(region_name="ap-southeast-2", access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY, config=None):
    """ Generates an returns an s3 client with the given credentials """
    session = boto3.session.Session(region_name=region_name,
                                    aws_access_key_id=access_key,
                                    aws_secret_access_key=secret_key)
    if config is None:
        client = session.client('s3')
    else:
        client = session.client('s3', config=config)
    return client


def generate_file_presigned_url(filename, client_method="put_object", bucket=settings.AWS_STORAGE_BUCKET_NAME):
    """ Returns the presigned url required to download/upload files from s3
    	Client Method = put_object for upload || get_object for download urls
    """
    client = generate_s3_client(config=boto3.session.Config(signature_version='s3v4'))
    # Generating the presigned url for the given filename
    presigned_url =  client.generate_presigned_url(
        ClientMethod=client_method,
        Params={
            'Bucket': bucket,
            'Key': filename,
        }
    )

    return presigned_url


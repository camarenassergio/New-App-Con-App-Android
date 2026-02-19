import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

def test_r2():
    print(f"Testing connection to: {ENDPOINT_URL}")
    print(f"Bucket: {BUCKET_NAME}")
    
    s3 = boto3.client(
        's3',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name='us-east-1', # Try explicit region
        # config=boto3.session.Config(signature_version='s3v4') # Implicit in many versions but good to be explicit
    )

    try:
        print("\nListing buckets...")
        response = s3.list_buckets()
        print("Buckets found:")
        for bucket in response['Buckets']:
            print(f" - {bucket['Name']}")
            
        print(f"\nChecking specific bucket: {BUCKET_NAME}...")
        s3.head_bucket(Bucket=BUCKET_NAME)
        print("Bucket exists and is accessible.")
        
        print("\nAttempting upload test...")
        s3.put_object(Bucket=BUCKET_NAME, Key='test_upload.txt', Body=b'Hello R2!')
        print("Upload successful!")
        
        print("\nAttempting head_object test...")
        s3.head_object(Bucket=BUCKET_NAME, Key='test_upload.txt')
        print("Head object successful!")

    except ClientError as e:
        print(f"\nERROR: {e}")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    test_r2()

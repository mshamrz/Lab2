import boto3
import json
import time

iam = boto3.client('iam', region_name='us-east-1')
glue = boto3.client('glue', region_name='us-east-1')

ROLE_NAME = 'AWSGlueServiceRole-payments-lab8'

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "glue.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

try:
    role = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    print("Created role:", ROLE_NAME)
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole")
    iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess")
    print("Attached policies. Waiting 10s for propagation...")
    time.sleep(10)
    role_arn = role['Role']['Arn']
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
    print("Using existing role:", role_arn)

CRAWLER_NAME = 'payments-crawler'
try:
    glue.create_crawler(
        Name=CRAWLER_NAME,
        Role=role_arn,
        DatabaseName='payments_db',
        TablePrefix='crawler_',
        Targets={
            'S3Targets': [
                {'Path': 's3://ucu-ooad-lab8-mshamrz-438424053032/payments/'}
            ]
        }
    )
    print("Crawler created:", CRAWLER_NAME)
except glue.exceptions.AlreadyExistsException:
    print("Crawler already exists")

print("Starting crawler...")
try:
    glue.start_crawler(Name=CRAWLER_NAME)
except Exception as e:
    print("Start crawler message:", e)

while True:
    c = glue.get_crawler(Name=CRAWLER_NAME)['Crawler']
    state = c['State']
    print(f"Crawler state: {state}")
    if state == 'READY':
        break
    time.sleep(5)

print("Crawler completed! Checking generated tables in payments_db...")
tables = glue.get_tables(DatabaseName='payments_db')['TableList']
crawler_tables = [t for t in tables if t['Name'].startswith('crawler_')]
for t in crawler_tables:
    print(f"\nTable: {t['Name']}")
    print("Partition keys:", t.get('PartitionKeys', []))
    print("Columns:")
    for col in t.get('StorageDescriptor', {}).get('Columns', []):
        print(f"  {col['Name']}: {col['Type']}")

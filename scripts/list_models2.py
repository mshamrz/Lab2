import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")
resp = bedrock.list_foundation_models(byProvider="Anthropic")
for m in resp["modelSummaries"]:
    print(m["modelId"])
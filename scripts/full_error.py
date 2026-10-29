import boto3

brt = boto3.client("bedrock-runtime", region_name="us-east-1")
try:
    brt.converse(
        modelId="anthropic.claude-haiku-5-5",
        messages=[{"role": "user", "content": [{"text": "Say hi"}]}],
        inferenceConfig={"maxTokens": 20},
    )
except Exception as e:
    print(e)
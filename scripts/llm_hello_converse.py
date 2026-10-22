import boto3

brt = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = brt.converse(
    modelId="us.anthropic.claude-opus-5-5-v1:0",
    messages=[{"role": "user", "content": [{"text": "In one sentence: what is an ISO week?"}]}],
    inferenceConfig={"maxTokens": 200},
)
print(resp["output"]["message"]["content"][0]["text"])
print(resp["usage"])

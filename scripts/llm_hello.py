import os
import boto3

MODEL = os.environ.get("PARSER_MODEL", "us.anthropic.claude-sonnet-4-6")
print("Model:", MODEL)

brt = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = brt.converse(
    modelId=MODEL,
    messages=[{"role": "user", "content": [{"text": "In one sentence: what is an ISO week?"}]}],
    inferenceConfig={"maxTokens": 1024},
)
print(resp["output"]["message"]["content"][0]["text"])
print(resp["stopReason"], resp["usage"]["inputTokens"], resp["usage"]["outputTokens"])
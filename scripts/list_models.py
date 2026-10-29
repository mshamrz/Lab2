from anthropic import AnthropicBedrockMantle

client = AnthropicBedrockMantle(aws_region="us-east-1")
try:
    for m in client.models.list():
        print(m.id)
except Exception as e:
    print(type(e).__name__, str(e)[:300])
from anthropic import AnthropicBedrockMantle

client = AnthropicBedrockMantle(aws_region="us-east-1")
for m in ["anthropic.claude-sonnet-5", "anthropic.claude-opus-5",
          "anthropic.claude-opus-4-8", "anthropic.claude-opus-4-7",
          "anthropic.claude-sonnet-4-6", "anthropic.claude-haiku-4-5-20251001-v1:0"]:
    try:
        client.messages.create(model=m, max_tokens=20,
                               messages=[{"role": "user", "content": "Say hi"}])
        print("OK  ", m)
    except Exception as e:
        print("FAIL", m, "->", type(e).__name__, str(e)[:150])
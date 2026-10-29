from anthropic import AnthropicBedrockMantle

client = AnthropicBedrockMantle(aws_region="us-east-1")
candidates = [
    "anthropic.claude-sonnet-5-5",
    "anthropic.claude-haiku-5-5",
    "anthropic.claude-opus-5-5",
    "claude-sonnet-5-5",
    "claude-haiku-5-5",
]
for m in candidates:
    try:
        r = client.messages.create(
            model=m, max_tokens=50,
            messages=[{"role": "user", "content": "Say hi"}],
        )
        print("OK  ", m)
    except Exception as e:
        print("FAIL", m, "->", type(e).__name__, str(e)[:120])
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")
brt = boto3.client("bedrock-runtime", region_name="us-east-1")

models = [
    "anthropic.claude-haiku-5-5",
    "anthropic.claude-sonnet-5-5",
    "anthropic.claude-opus-5-5",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-sonnet-4-6",
]

for m in models:
    print("==", m)
    try:
        a = bedrock.get_foundation_model_availability(modelId=m)
        print("  auth:", a.get("authorizationStatus"),
              "| entitlement:", a.get("entitlementAvailability"),
              "| agreement:", a.get("agreementAvailability", {}).get("status"))
    except Exception as e:
        print("  availability:", type(e).__name__, str(e)[:100])
    for mid in (m, "us." + m):
        try:
            r = brt.converse(
                modelId=mid,
                messages=[{"role": "user", "content": [{"text": "Say hi"}]}],
                inferenceConfig={"maxTokens": 20},
            )
            print("  converse OK:", mid)
            break
        except Exception as e:
            print("  converse FAIL:", mid, "->", type(e).__name__, str(e)[:90])
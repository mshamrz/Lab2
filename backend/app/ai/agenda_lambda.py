import base64
import json
import logging
import os
import time
from datetime import date

import jwt  # PyJWT
from botocore.exceptions import ClientError

from app.ai.agenda import PARSER_MODEL, PROMPT_VERSION, AgendaParseError, parse_agenda

log = logging.getLogger()
log.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "us-east-1")
USER_POOL_ID = os.environ["USER_POOL_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
jwks = jwt.PyJWKClient(f"{ISSUER}/.well-known/jwks.json")

MAX_CHARS = 10_000

# USD per 1M tokens (input, output). Check the Bedrock price page and fix if needed.
PRICES = {
    "us.anthropic.claude-sonnet-4-6": (3.00, 15.00),
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": (1.00, 5.00),
}


class Unauthorized(Exception):
    pass


def verify_cognito_token(header: str) -> dict:
    if not header.lower().startswith("bearer "):
        raise Unauthorized("missing bearer token")
    token = header[7:].strip()
    try:
        key = jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256"], issuer=ISSUER,
            options={"verify_aud": False},
        )
    except Exception as e:
        raise Unauthorized(f"{type(e).__name__}: {e}")
    use = claims.get("token_use")
    if use == "id":
        ok = claims.get("aud") == CLIENT_ID
    elif use == "access":
        ok = claims.get("client_id") == CLIENT_ID
    else:
        ok = False
    if not ok:
        raise Unauthorized("token was issued for another client")
    return claims


def cost_usd(model: str, usage: dict) -> float:
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return round(
        usage["input_tokens"] * price_in / 1e6 + usage["output_tokens"] * price_out / 1e6, 6
    )


def reply(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def handler(event, context):
    try:
        user = verify_cognito_token(event.get("headers", {}).get("authorization", ""))
    except Unauthorized as e:
        log.warning("unauthorized: %s", e)
        return reply(401, {"error": "unauthorized"})

    try:
        raw = event.get("body") or ""
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode("utf-8")
        body = json.loads(raw)
        text = body["text"]
        today = date.fromisoformat(body["today"])
        tz = body["tz"]
    except Exception:
        return reply(400, {"error": "expected JSON with text, today (YYYY-MM-DD) and tz"})

    if not isinstance(text, str) or not text.strip():
        return reply(400, {"error": "text is empty"})
    if len(text) > MAX_CHARS:
        return reply(413, {"error": f"text is longer than {MAX_CHARS} characters"})

    started = time.monotonic()
    try:
        agenda, usage = parse_agenda(text, today, tz)
    except AgendaParseError as e:
        return reply(422, {"error": str(e)})
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ThrottlingException":
            return reply(429, {"error": "the service is busy, try again in a minute"})
        log.exception("bedrock error")
        return reply(502, {"error": "the model is unavailable"})

    log.info(json.dumps({
        "event": "agenda_parsed",
        "user": user.get("sub"),
        "model": PARSER_MODEL,
        "prompt_version": PROMPT_VERSION,
        **usage,
        "latency_ms": int((time.monotonic() - started) * 1000),
        "cost_usd": cost_usd(PARSER_MODEL, usage),
    }))
    return reply(200, {
        "agenda": agenda.model_dump(mode="json"),
        "model": PARSER_MODEL,
        "prompt_version": PROMPT_VERSION,
    })
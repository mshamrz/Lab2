import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date

URL = "https://dwnx3qwwptlomoucjjtrac2eky0ydplh.lambda-url.us-east-1.on.aws/"


def load_token() -> str:
    """Token from PARSER_TOKEN, or the id_token saved in token.json by curl."""
    token = os.environ.get("PARSER_TOKEN")
    if token:
        return token.strip()
    with open("token.json", encoding="utf-8") as f:
        return json.load(f)["id_token"]


text = " ".join(sys.argv[1:]) or (
    "Пн 10:00, синк по прайсингу, 45 хв. 1) нові тарифи Pro — Олена, 15 хв "
    "2) фідбек від клієнтів — Taras 3) що робимо з річною знижкою. "
    "Taras до п'ятниці збирає порівняння з конкурентами."
)

body = json.dumps(
    {"text": text, "today": date.today().isoformat(), "tz": "Europe/Kyiv"}
).encode("utf-8")
req = urllib.request.Request(
    URL,
    data=body,
    method="POST",
    headers={
        "content-type": "application/json",
        "authorization": "Bearer " + load_token(),
    },
)

try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("HTTP", r.status)
        print(json.dumps(json.loads(r.read()), ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode("utf-8"))
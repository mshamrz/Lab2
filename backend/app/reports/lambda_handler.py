import logging
import os
from datetime import date, timedelta

import boto3

from app.database import SessionLocal
from app.reports.weekly import build_weekly_report

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

REPORTS_BUCKET = os.environ["REPORTS_BUCKET"]

s3 = boto3.client("s3")


def _previous_iso_week() -> str:
    today = date.today()
    last_week_day = today - timedelta(days=7)
    iso_year, iso_week, _ = last_week_day.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _detect_trigger(event: dict) -> str:
    if isinstance(event, dict) and "Records" in event:
        return "sqs"
    if isinstance(event, dict) and event.get("source") == "schedule":
        return "schedule"
    return "direct"


def _week_from_event(event: dict) -> str | None:
    if isinstance(event, dict) and "Records" in event:
        import json

        body = json.loads(event["Records"][0]["body"])
        return body.get("week")
    if isinstance(event, dict):
        return event.get("week")
    return None


def handler(event, context):
    trigger = _detect_trigger(event)
    week = _week_from_event(event) or _previous_iso_week()

    log.info("report-builder triggered", extra={"trigger": trigger, "week": week})

    db = SessionLocal()
    try:
        csv_bytes = build_weekly_report(db, week)
    finally:
        db.close()

    key = f"reports/{week}.csv"
    s3.put_object(Bucket=REPORTS_BUCKET, Key=key, Body=csv_bytes, ContentType="text/csv")

    log.info("report-builder wrote report", extra={"bucket": REPORTS_BUCKET, "key": key})

    return {"bucket": REPORTS_BUCKET, "key": key, "week": week}

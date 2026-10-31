import os, boto3, logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

log = logging.getLogger()
log.setLevel(logging.INFO)
s3 = boto3.client('s3')
ses = boto3.client('ses')

def handler(event, context):
    log.info("report-mailer triggered", extra={"trigger": "s3", "event": event})
    record = event['Records'][0]['s3']
    bucket = record['bucket']['name']
    key = record['object']['key']

    obj = s3.get_object(Bucket=bucket, Key=key)
    file_bytes = obj['Body'].read()

    recipient = os.environ['RECIPIENT_EMAIL']
    sender = os.environ.get('SENDER_EMAIL', recipient)

    msg = MIMEMultipart()
    msg['Subject'] = f"Weekly Meetings Report ({os.path.basename(key)})"
    msg['From'] = sender
    msg['To'] = recipient

    msg.attach(MIMEText("Please find attached the requested weekly report CSV file.", "plain"))
    att = MIMEApplication(file_bytes)
    att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(key))
    msg.attach(att)

    ses.send_raw_email(Source=sender, Destinations=[recipient], RawMessage={'Data': msg.as_bytes()})
    log.info("report-mailer sent email", extra={"recipient": recipient, "key": key})
    return {"status": "sent", "key": key}

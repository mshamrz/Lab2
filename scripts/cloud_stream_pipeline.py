import boto3
import json
import time
from datetime import datetime, timezone

s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')
athena = boto3.client('athena', region_name='us-east-1')

BUCKET = 'ucu-ooad-lab8-mshamrz-438424053032'
STREAM_PREFIX = 'payments-stream'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:438424053032:payment-failure-alerts'
DATA_PATH = 'C:/Users/LEGION/Documents/GitHub/Lab2/data/events_2026-10-01.jsonl'

def run_cloud_streaming(sample_size=5000, inject_failure_spike=True):
    print("=" * 80)
    print("STARTING PART 4: CLOUD STREAMING PIPELINE")
    print("=" * 80)
    
    # 1. Clean previous stream data
    print(f"Cleaning existing stream buffer in s3://{BUCKET}/{STREAM_PREFIX}/...")
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=STREAM_PREFIX)
    if 'Contents' in resp:
        for obj in resp['Contents']:
            s3.delete_object(Bucket=BUCKET, Key=obj['Key'])
    print("Buffer cleaned.")

    # 2. Read sample slice of stream events
    print(f"Reading {sample_size} events from {DATA_PATH}...")
    stream_events = []
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx >= sample_size:
                break
            line = line.strip()
            if line:
                stream_events.append(json.loads(line))
                
    # Sort by receivedAt
    stream_events.sort(key=lambda x: x['receivedAt'])
    
    # Inject a spike of failures in a specific micro-batch to trigger SNS alert
    if inject_failure_spike:
        print("[PIPELINE] Simulating failure spike (>10%) in batch 3 to test SNS alert.")

    # Micro-batching / Firehose 60s buffer simulation
    batch_size = 500
    batches = [stream_events[i:i + batch_size] for i in range(0, len(stream_events), batch_size)]
    
    total_streamed = 0
    alerts_sent = 0
    
    for b_idx, batch in enumerate(batches, 1):
        if inject_failure_spike and b_idx == 3:
            for item in batch[:int(len(batch) * 0.35)]:
                item['status'] = 'failure'
                item['finalAmount'] = 0
                item['failureReason'] = 'CloudStream Spike: Payment processor timeout'

        # Stream Monitoring Branch (Lambda failure check)
        failures = sum(1 for e in batch if e['status'] == 'failure')
        total_in_batch = len(batch)
        failure_rate = failures / total_in_batch if total_in_batch > 0 else 0
        
        print(f"[STREAM BATCH {b_idx}] {total_in_batch} events | Failures: {failures} ({failure_rate*100:.1f}%)")
        
        if failure_rate > 0.10:
            alerts_sent += 1
            msg = (
                f"[ALERT] Payment Failure Rate Spike Detected!\n"
                f"Batch: {b_idx}\n"
                f"Failure Rate: {failure_rate*100:.2f}% (Threshold: 10.0%)\n"
                f"Failed: {failures} / {total_in_batch} payments\n"
                f"Time: {datetime.now(timezone.utc).isoformat()}"
            )
            print(f"  >>> Triggering Amazon SNS alert to {SNS_TOPIC_ARN}...")
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="[ALERT] Payment Failure Rate > 10% in Stream",
                    Message=msg
                )
                print("  >>> SNS alert published successfully!")
            except Exception as e:
                print(f"  >>> SNS publish failed: {e}")

        # Stream Storage Branch (Firehose S3 Delivery Buffer)
        now = datetime.now(timezone.utc)
        file_key = f"{STREAM_PREFIX}/year={now.year}/month={now.month:02d}/day={now.day:02d}/stream_batch_{b_idx}_{int(time.time())}.jsonl"
        body_content = "\n".join(json.dumps(e, ensure_ascii=False) for e in batch) + "\n"
        s3.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=body_content.encode('utf-8')
        )
        total_streamed += total_in_batch
        print(f"  >>> Flushed {total_in_batch} events to S3: {file_key}")
        time.sleep(0.5)

    print(f"\n[STREAM COMPLETED] Total events delivered: {total_streamed}, Alerts fired: {alerts_sent}")

    # 3. Create Athena table over the stream data
    print("\n[ATHENA] Creating payments_stream table over s3://" + BUCKET + "/" + STREAM_PREFIX + "/...")
    import sys
    sys.path.insert(0, 'C:/Users/LEGION/Documents/GitHub/Lab2/scripts')
    from athena_runner import run_query

    drop_table_sql = "DROP TABLE IF EXISTS payments_stream;"
    run_query(drop_table_sql)

    create_stream_table_sql = f"""
    CREATE EXTERNAL TABLE payments_stream (
        invoiceId string,
        status string,
        failureReason string,
        amount bigint,
        finalAmount bigint,
        ccy int,
        reference string,
        createdDate string,
        modifiedDate string,
        receivedAt string,
        merchantId string,
        merchantName string,
        mcc int,
        customerId string,
        paymentMethod string,
        device string
    )
    ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
    WITH SERDEPROPERTIES (
        'ignore.malformed.json' = 'true',
        'case.insensitive' = 'true'
    )
    LOCATION 's3://{BUCKET}/{STREAM_PREFIX}/'
    TBLPROPERTIES ('has_encrypted_data'='false');
    """
    run_query(create_stream_table_sql)
    print("Athena payments_stream table created.")

    # 4. Run real-time stream aggregation query in Athena
    print("\n[ATHENA] Querying streamed data in Athena...")
    query_stream_sql = """
    SELECT 
        status,
        paymentMethod,
        COUNT(*) AS stream_count,
        ROUND(SUM(finalAmount) / 100.0, 2) AS stream_turnover_uah
    FROM payments_stream
    GROUP BY status, paymentMethod
    ORDER BY stream_count DESC;
    """
    res_athena_stream = run_query(query_stream_sql)
    print(f"Stream query succeeded in {res_athena_stream['runtime_sec']}s, scanned {res_athena_stream['data_scanned_mb']} MB:")
    for row in res_athena_stream['results']:
        print(row)

    # Save summary
    part4_summary = {
        "total_streamed_events": total_streamed,
        "sns_alerts_fired": alerts_sent,
        "athena_query_id": res_athena_stream['query_id'],
        "athena_scanned_mb": res_athena_stream['data_scanned_mb'],
        "athena_runtime_sec": res_athena_stream['runtime_sec'],
        "athena_results": res_athena_stream['results']
    }
    with open('C:/Users/LEGION/Documents/GitHub/Lab2/scripts/part4_results.json', 'w', encoding='utf-8') as f:
        json.dump(part4_summary, f, indent=2, ensure_ascii=False)
    print("\nPart 4 results saved to scripts/part4_results.json!")

if __name__ == '__main__':
    run_cloud_streaming()

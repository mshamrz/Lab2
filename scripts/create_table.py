import sys
from athena_runner import run_query

create_table_sql = """
CREATE EXTERNAL TABLE IF NOT EXISTS payment_events (
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
PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES (
    'ignore.malformed.json' = 'true',
    'case.insensitive' = 'true'
)
LOCATION 's3://ucu-ooad-lab8-mshamrz-438424053032/payments/'
TBLPROPERTIES ('has_encrypted_data'='false');
"""

print("Creating payment_events table...")
res = run_query(create_table_sql)
print("Table created:", res['query_id'])

print("Repairing table (discovering partitions)...")
res_mscck = run_query("MSCK REPAIR TABLE payment_events;")
print("Partitions loaded:", res_mscck['query_id'])

print("Running COUNT(*)...")
res_count = run_query("SELECT COUNT(*) AS total_events, COUNT(DISTINCT dt) AS days_count FROM payment_events;")
print("Count result:", res_count['results'])
print(f"Data scanned: {res_count['data_scanned_mb']} MB, Time: {res_count['runtime_sec']} s")

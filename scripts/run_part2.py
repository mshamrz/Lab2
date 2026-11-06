import sys
import json
import csv
import time
sys.path.insert(0, 'C:/Users/LEGION/Documents/GitHub/Lab2/scripts')
from athena_runner import run_query

print("=== RUNNING QUERY 3 (JSON): Turnover by merchant & currency ===")
q3_sql = """
SELECT 
    merchantId,
    merchantName,
    CASE ccy
        WHEN 980 THEN 'UAH'
        WHEN 840 THEN 'USD'
        WHEN 978 THEN 'EUR'
        ELSE CAST(ccy AS varchar)
    END AS currency,
    COUNT(*) AS successful_payments_count,
    ROUND(SUM(finalAmount) / 100.0, 2) AS total_turnover
FROM payments
WHERE status = 'success'
GROUP BY merchantId, merchantName, ccy
ORDER BY total_turnover DESC;
"""
res_q3_json = run_query(q3_sql)
print(f"Q3 JSON: Scanned {res_q3_json['data_scanned_mb']} MB, Time: {res_q3_json['runtime_sec']}s")
print("Results:")
for r in res_q3_json['results']:
    print(r)

print("\n=== RUNNING QUERY 4 (JSON): Failure rate by method & device ===")
q4_sql = """
SELECT 
    paymentMethod,
    device,
    COUNT(*) AS total_payments,
    COUNT(CASE WHEN status = 'failure' THEN 1 END) AS failed_payments,
    ROUND(100.0 * COUNT(CASE WHEN status = 'failure' THEN 1 END) / COUNT(*), 2) AS failure_rate_pct
FROM payments
GROUP BY paymentMethod, device
ORDER BY failure_rate_pct DESC;
"""
res_q4_json = run_query(q4_sql)
print(f"Q4 JSON: Scanned {res_q4_json['data_scanned_mb']} MB, Time: {res_q4_json['runtime_sec']}s")
print("Results:")
for r in res_q4_json['results']:
    print(r)

print("\n=== RUNNING QUERY 5 (JSON): Peak hours ===")
q5_sql = """
SELECT 
    hour(from_iso8601_timestamp(createdDate)) AS hour_of_day,
    COUNT(*) AS payments_count
FROM payments
GROUP BY 1
ORDER BY 1 ASC;
"""
res_q5_json = run_query(q5_sql)
print(f"Q5 JSON: Scanned {res_q5_json['data_scanned_mb']} MB, Time: {res_q5_json['runtime_sec']}s")
print("Results:")
for r in res_q5_json['results']:
    print(r)

print("\n=== RUNNING QUERY 6: Late events ===")
q6_sql = """
SELECT 
    COUNT(*) AS total_events,
    COUNT(CASE WHEN date_diff('second', from_iso8601_timestamp(modifiedDate), from_iso8601_timestamp(receivedAt)) > 60 THEN 1 END) AS late_events_gt_60s,
    ROUND(100.0 * COUNT(CASE WHEN date_diff('second', from_iso8601_timestamp(modifiedDate), from_iso8601_timestamp(receivedAt)) > 60 THEN 1 END) / COUNT(*), 4) AS late_pct
FROM payment_events;
"""
res_q6 = run_query(q6_sql)
print("Q6 results:", res_q6['results'])

print("\n=== EXECUTING CTAS: Creating Parquet table payments_curated ===")
ctas_drop_sql = "DROP TABLE IF EXISTS payments_curated;"
run_query(ctas_drop_sql)

ctas_sql = """
CREATE TABLE payments_curated
WITH (
    format = 'PARQUET',
    parquet_compression = 'SNAPPY',
    external_location = 's3://ucu-ooad-lab8-mshamrz-438424053032/curated/',
    partitioned_by = ARRAY['dt']
) AS
SELECT 
    invoiceId,
    status,
    failureReason,
    amount,
    finalAmount,
    ccy,
    reference,
    createdDate,
    modifiedDate,
    receivedAt,
    merchantId,
    merchantName,
    mcc,
    customerId,
    paymentMethod,
    device,
    dt
FROM payments;
"""
t0 = time.time()
res_ctas = run_query(ctas_sql)
print(f"CTAS finished in {round(time.time() - t0, 2)}s, query id: {res_ctas['query_id']}")

print("\n=== RUNNING QUERIES 3, 4, 5 ON PARQUET TABLE ===")
q3_parquet = """
SELECT 
    merchantId,
    merchantName,
    CASE ccy
        WHEN 980 THEN 'UAH'
        WHEN 840 THEN 'USD'
        WHEN 978 THEN 'EUR'
        ELSE CAST(ccy AS varchar)
    END AS currency,
    COUNT(*) AS successful_payments_count,
    ROUND(SUM(finalAmount) / 100.0, 2) AS total_turnover
FROM payments_curated
WHERE status = 'success'
GROUP BY merchantId, merchantName, ccy
ORDER BY total_turnover DESC;
"""
res_q3_parquet = run_query(q3_parquet)
print(f"Q3 Parquet: Scanned {res_q3_parquet['data_scanned_mb']} MB, Time: {res_q3_parquet['runtime_sec']}s")

q4_parquet = """
SELECT 
    paymentMethod,
    device,
    COUNT(*) AS total_payments,
    COUNT(CASE WHEN status = 'failure' THEN 1 END) AS failed_payments,
    ROUND(100.0 * COUNT(CASE WHEN status = 'failure' THEN 1 END) / COUNT(*), 2) AS failure_rate_pct
FROM payments_curated
GROUP BY paymentMethod, device
ORDER BY failure_rate_pct DESC;
"""
res_q4_parquet = run_query(q4_parquet)
print(f"Q4 Parquet: Scanned {res_q4_parquet['data_scanned_mb']} MB, Time: {res_q4_parquet['runtime_sec']}s")

q5_parquet = """
SELECT 
    hour(from_iso8601_timestamp(createdDate)) AS hour_of_day,
    COUNT(*) AS payments_count
FROM payments_curated
GROUP BY 1
ORDER BY 1 ASC;
"""
res_q5_parquet = run_query(q5_parquet)
print(f"Q5 Parquet: Scanned {res_q5_parquet['data_scanned_mb']} MB, Time: {res_q5_parquet['runtime_sec']}s")

# Save summary
summary = {
    "comparison": [
        {
            "query": "Query 3 (Turnover)",
            "json_scanned_mb": res_q3_json['data_scanned_mb'],
            "json_runtime_s": res_q3_json['runtime_sec'],
            "parquet_scanned_mb": res_q3_parquet['data_scanned_mb'],
            "parquet_runtime_s": res_q3_parquet['runtime_sec'],
            "scanned_ratio": round(res_q3_json['data_scanned_mb'] / max(res_q3_parquet['data_scanned_mb'], 0.001), 1)
        },
        {
            "query": "Query 4 (Failure Rate)",
            "json_scanned_mb": res_q4_json['data_scanned_mb'],
            "json_runtime_s": res_q4_json['runtime_sec'],
            "parquet_scanned_mb": res_q4_parquet['data_scanned_mb'],
            "parquet_runtime_s": res_q4_parquet['runtime_sec'],
            "scanned_ratio": round(res_q4_json['data_scanned_mb'] / max(res_q4_parquet['data_scanned_mb'], 0.001), 1)
        },
        {
            "query": "Query 5 (Peak Hours)",
            "json_scanned_mb": res_q5_json['data_scanned_mb'],
            "json_runtime_s": res_q5_json['runtime_sec'],
            "parquet_scanned_mb": res_q5_parquet['data_scanned_mb'],
            "parquet_runtime_s": res_q5_parquet['runtime_sec'],
            "scanned_ratio": round(res_q5_json['data_scanned_mb'] / max(res_q5_parquet['data_scanned_mb'], 0.001), 1)
        }
    ],
    "q3_results": res_q3_parquet['results'],
    "q4_results": res_q4_parquet['results'],
    "q5_results": res_q5_parquet['results'],
    "q6_results": res_q6['results']
}

with open('C:/Users/LEGION/Documents/GitHub/Lab2/scripts/part2_results.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("\n=== ALL PART 2 QUERIES COMPLETED & SAVED ===")

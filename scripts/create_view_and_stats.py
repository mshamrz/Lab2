import sys
sys.path.insert(0, 'C:/Users/LEGION/Documents/GitHub/Lab2/scripts')
from athena_runner import run_query

view_sql = """
CREATE OR REPLACE VIEW payments AS
WITH distinct_events AS (
    SELECT DISTINCT
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
    FROM payment_events
),
ranked AS (
    SELECT *,
           row_number() OVER (
               PARTITION BY invoiceId 
               ORDER BY modifiedDate DESC, receivedAt DESC
           ) as rn
    FROM distinct_events
)
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
FROM ranked
WHERE rn = 1;
"""

print("Creating view payments...")
run_query(view_sql)
print("View created successfully!")

stats_sql = """
SELECT 
    (SELECT COUNT(*) FROM payment_events) AS total_events,
    (SELECT COUNT(*) FROM (SELECT DISTINCT invoiceId, status, failureReason, amount, finalAmount, ccy, reference, createdDate, modifiedDate, receivedAt, merchantId, merchantName, mcc, customerId, paymentMethod, device, dt FROM payment_events)) AS distinct_events,
    (SELECT COUNT(*) FROM payments) AS unique_invoices,
    (SELECT COUNT(DISTINCT invoiceId) FROM payment_events) AS distinct_invoices_check;
"""

print("Calculating scale stats...")
stats = run_query(stats_sql)
print("Scale stats:", stats['results'])
print(f"Data scanned: {stats['data_scanned_mb']} MB, Time: {stats['runtime_sec']} s")

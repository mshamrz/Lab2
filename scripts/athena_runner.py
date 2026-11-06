import boto3
import time
import json
import csv

athena = boto3.client('athena', region_name='us-east-1')

DATABASE = 'payments_db'
OUTPUT_LOCATION = 's3://ucu-ooad-lab8-mshamrz-438424053032/athena-results/'

def run_query(sql, database=DATABASE):
    ctx = {'Database': database or 'default'}
    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext=ctx,
        ResultConfiguration={'OutputLocation': OUTPUT_LOCATION}
    )
    qid = resp['QueryExecutionId']
    while True:
        status_resp = athena.get_query_execution(QueryExecutionId=qid)
        state = status_resp['QueryExecution']['Status']['State']
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
        
    if state != 'SUCCEEDED':
        reason = status_resp['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        raise RuntimeError(f"Query {qid} {state}: {reason}\nSQL:\n{sql}")
        
    stats = status_resp['QueryExecution']['Statistics']
    data_scanned_bytes = stats.get('DataScannedInBytes', 0)
    exec_time_ms = stats.get('EngineExecutionTimeInMillis', 0)
    
    # fetch results
    results = []
    paginator = athena.get_paginator('get_query_results')
    col_names = []
    first_page = True
    for page in paginator.paginate(QueryExecutionId=qid):
        rows = page['ResultSet']['Rows']
        if first_page and rows:
            col_names = [col.get('VarCharValue', '') for col in rows[0]['Data']]
            rows = rows[1:]
            first_page = False
        for row in rows:
            vals = [col.get('VarCharValue', None) for col in row['Data']]
            results.append(dict(zip(col_names, vals)))
            
    return {
        'query_id': qid,
        'data_scanned_mb': round(data_scanned_bytes / (1024 * 1024), 2),
        'data_scanned_bytes': data_scanned_bytes,
        'runtime_sec': round(exec_time_ms / 1000, 2),
        'row_count': len(results),
        'results': results
    }

if __name__ == '__main__':
    print("Creating database payments_db...")
    res = run_query("CREATE DATABASE IF NOT EXISTS payments_db;", database=None)
    print("Database created:", res)

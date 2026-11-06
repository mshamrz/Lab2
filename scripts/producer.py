import json
import time
import argparse
import random
from datetime import datetime

def load_events(file_path, limit=None):
    events = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            line = line.strip()
            if line:
                events.append(json.loads(line))
    # Sort strictly by receivedAt to replicate arrival order (processing time)
    events.sort(key=lambda x: x['receivedAt'])
    return events

def run_producer(file_path, broker=None, topic='payments', rate=20, fail_rate=0.0, limit=None, output_queue=None):
    print(f"[PRODUCER] Loading events from {file_path}...")
    events = load_events(file_path, limit=limit)
    total = len(events)
    print(f"[PRODUCER] Loaded {total} events. Sorted by receivedAt.")
    if fail_rate > 0:
        print(f"[PRODUCER] EXPERIMENT 3 MODE: Injecting {fail_rate*100:.0f}% payment failures.")

    kafka_producer = None
    if broker:
        try:
            from kafka import KafkaProducer
            kafka_producer = KafkaProducer(
                bootstrap_servers=broker,
                key_serializer=lambda k: k.encode('utf-8') if isinstance(k, str) else k,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print(f"[PRODUCER] Connected to Kafka/Redpanda broker at {broker}")
        except Exception as e:
            print(f"[PRODUCER] Warning: Could not connect to Kafka ({e}).")

    delay = 1.0 / rate if rate > 0 else 0
    invoices_to_fail = set()
    
    # If fail_rate is requested, pre-select invoices to fail
    if fail_rate > 0:
        unique_invoices = list(set(e['invoiceId'] for e in events))
        num_fail = int(len(unique_invoices) * fail_rate)
        invoices_to_fail = set(random.sample(unique_invoices, num_fail))

    sent = 0
    start_time = time.time()
    for e in events:
        inv_id = e['invoiceId']
        # Apply failure injection if selected
        if inv_id in invoices_to_fail and e['status'] in ['processing', 'success']:
            e = dict(e)
            e['status'] = 'failure'
            e['finalAmount'] = 0
            e['failureReason'] = 'Simulated high-failure injection'

        # Send to Kafka if available
        if kafka_producer:
            kafka_producer.send(topic, key=inv_id, value=e)
        
        # Send to in-memory queue if provided
        if output_queue is not None:
            output_queue.put((inv_id, e))

        sent += 1
        if sent % 1000 == 0 or sent == total:
            elapsed = time.time() - start_time
            print(f"[PRODUCER] Replayed {sent}/{total} events ({sent/max(elapsed, 0.001):.1f} eps)")

        if delay > 0:
            time.sleep(delay)

    if kafka_producer:
        kafka_producer.flush()
    print(f"[PRODUCER] Completed publishing {sent} events.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Replay payment events into Redpanda/Kafka")
    parser.add_argument('--file', default='C:/Users/LEGION/Documents/GitHub/Lab2/data/events_2026-10-01.jsonl', help="Path to events.jsonl")
    parser.add_argument('--broker', default='localhost:19092', help="Kafka bootstrap broker")
    parser.add_argument('--topic', default='payments', help="Topic name")
    parser.add_argument('--rate', type=float, default=100, help="Events per second (0 for max speed)")
    parser.add_argument('--fail-rate', type=float, default=0.0, help="Fraction of payments to force to failure (0.0 to 1.0)")
    parser.add_argument('--limit', type=int, default=None, help="Limit number of events to send")
    args = parser.parse_args()

    run_producer(args.file, broker=args.broker, topic=args.topic, rate=args.rate, fail_rate=args.fail_rate, limit=args.limit)

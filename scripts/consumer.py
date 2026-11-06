import json
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def parse_iso(dt_str):
    # e.g. "2026-10-01T14:29:23Z"
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    return datetime.fromisoformat(dt_str)

class PaymentWindowConsumer:
    def __init__(self, consumer_id="C1", allowed_lateness_minutes=2.0, alert_threshold=0.10):
        self.consumer_id = consumer_id
        self.allowed_lateness = timedelta(minutes=allowed_lateness_minutes)
        self.alert_threshold = alert_threshold
        
        # Deduplication cache
        self.seen_events = set()
        
        # Windows: window_start -> { paymentMethod -> { invoiceId -> final_status } }
        self.windows = defaultdict(lambda: defaultdict(dict))
        
        self.watermark = None
        self.closed_windows = set()
        
        # Stats
        self.total_received = 0
        self.total_duplicates_dropped = 0
        self.total_late_rejected = 0
        self.total_alerts = 0
        self.closed_window_summaries = []

    def process_event(self, event):
        self.total_received += 1
        
        inv_id = event['invoiceId']
        mod_date_str = event['modifiedDate']
        status = event['status']
        method = event.get('paymentMethod', 'unknown')
        
        # 1. Deduplication: drop exact duplicates
        event_sig = (inv_id, mod_date_str, status)
        if event_sig in self.seen_events:
            self.total_duplicates_dropped += 1
            return
        self.seen_events.add(event_sig)
        
        event_time = parse_iso(mod_date_str)
        if self.watermark is None or event_time > self.watermark:
            self.watermark = event_time
            
        # 1-minute tumbling window
        w_start = event_time.replace(second=0, microsecond=0)
        w_end = w_start + timedelta(minutes=1)
        
        # Check if window is already closed
        if w_start in self.closed_windows:
            self.total_late_rejected += 1
            return
            
        # Add to window state
        self.windows[w_start][method][inv_id] = status
        
        # Check and close mature windows
        self.advance_watermark()

    def advance_watermark(self):
        if self.watermark is None:
            return
            
        # Windows close when watermark >= window_end + allowed_lateness
        to_close = []
        for w_start in list(self.windows.keys()):
            w_end = w_start + timedelta(minutes=1)
            cutoff = w_end + self.allowed_lateness
            if self.watermark >= cutoff:
                to_close.append(w_start)
                
        to_close.sort()
        for w_start in to_close:
            self.close_window(w_start)

    def close_window(self, w_start):
        methods_data = self.windows.pop(w_start)
        self.closed_windows.add(w_start)
        w_end = w_start + timedelta(minutes=1)
        
        summary = {
            'window_start': w_start.isoformat(),
            'window_end': w_end.isoformat(),
            'methods': {}
        }
        
        total_window_payments = 0
        total_window_failures = 0
        
        for method, invoices in methods_data.items():
            tot = len(invoices)
            failed = sum(1 for st in invoices.values() if st == 'failure')
            rate = failed / tot if tot > 0 else 0.0
            
            summary['methods'][method] = {
                'total': tot,
                'failed': failed,
                'failure_rate': round(rate, 4)
            }
            total_window_payments += tot
            total_window_failures += failed
            
            if rate > self.alert_threshold and tot >= 10:
                self.total_alerts += 1
                print(f"[{self.consumer_id} ALERT] Window {w_start.strftime('%H:%M')} | Method: {method.upper()} "
                      f"FAILURE RATE {rate*100:.1f}% > {self.alert_threshold*100:.0f}% ({failed}/{tot} failed)")
                      
        summary['total_payments'] = total_window_payments
        summary['total_failures'] = total_window_failures
        self.closed_window_summaries.append(summary)

    def flush_remaining(self):
        for w_start in sorted(list(self.windows.keys())):
            self.close_window(w_start)

def run_consumer(broker='localhost:19092', topic='payments', group_id='payments-group', lateness_min=2.0):
    print(f"[CONSUMER] Starting consumer (group: {group_id}, lateness: {lateness_min} min)...")
    consumer_engine = PaymentWindowConsumer(consumer_id="C1", allowed_lateness_minutes=lateness_min)
    
    try:
        from kafka import KafkaConsumer
        kc = KafkaConsumer(
            topic,
            bootstrap_servers=broker,
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        print(f"[CONSUMER] Connected to Kafka {broker}, listening on topic '{topic}'...")
        for msg in kc:
            consumer_engine.process_event(msg.value)
    except Exception as e:
        print(f"[CONSUMER] Kafka error: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Payment window streaming consumer")
    parser.add_argument('--broker', default='localhost:19092')
    parser.add_argument('--topic', default='payments')
    parser.add_argument('--group', default='payments-group')
    parser.add_argument('--lateness', type=float, default=2.0, help="Allowed lateness in minutes")
    args = parser.parse_args()
    
    run_consumer(broker=args.broker, topic=args.topic, group_id=args.group, lateness_min=args.lateness)

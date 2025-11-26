"""
Windows Event Log Collector
Monitors Windows Event Logs and sends them to the Network Management System
"""

import win32evtlog
import win32evtlogutil
import win32con
import requests
import time
import json
from datetime import datetime
import socket

# Configuration
API_URL = "http://localhost:5000/api/logs/ingest"
POLL_INTERVAL = 10  # seconds
SOURCE_NAME = socket.gethostname()  # Use computer name as source

# Event log types to monitor
LOG_TYPES = {
    'Application': win32evtlog.EVENTLOG_ERROR_TYPE | win32evtlog.EVENTLOG_WARNING_TYPE,
    'System': win32evtlog.EVENTLOG_ERROR_TYPE | win32evtlog.EVENTLOG_WARNING_TYPE,
}

# Map Windows event types to our log levels
EVENT_TYPE_MAP = {
    win32evtlog.EVENTLOG_ERROR_TYPE: 'ERROR',
    win32evtlog.EVENTLOG_WARNING_TYPE: 'WARNING',
    win32evtlog.EVENTLOG_INFORMATION_TYPE: 'INFO',
    win32evtlog.EVENTLOG_AUDIT_FAILURE: 'CRITICAL',
    win32evtlog.EVENTLOG_AUDIT_SUCCESS: 'INFO',
}


class WindowsLogCollector:
    def __init__(self):
        self.last_record_numbers = {}
        self.session = requests.Session()
        
    def get_event_level(self, event_type):
        """Convert Windows event type to our log level"""
        return EVENT_TYPE_MAP.get(event_type, 'INFO')
    
    def read_events(self, log_type, flags):
        """Read events from Windows Event Log"""
        try:
            hand = win32evtlog.OpenEventLog(None, log_type)
            
            # Get total number of records
            total = win32evtlog.GetNumberOfEventLogRecords(hand)
            
            # Get last record number we processed
            last_processed = self.last_record_numbers.get(log_type, total - 1)
            
            # Read new events
            events = win32evtlog.ReadEventLog(
                hand,
                win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ,
                0
            )
            
            new_logs = []
            
            for event in events:
                # Only process events we haven't seen
                if event.RecordNumber <= last_processed:
                    break
                
                # Filter by event type
                if event.EventType & flags:
                    log_entry = {
                        'source': f"{SOURCE_NAME}/{log_type}",
                        'level': self.get_event_level(event.EventType),
                        'message': self.get_event_message(event),
                        'timestamp': event.TimeGenerated.isoformat(),
                        'metadata': {
                            'event_id': event.EventID,
                            'event_category': event.EventCategory,
                            'source_name': event.SourceName,
                            'computer': event.ComputerName,
                        }
                    }
                    new_logs.append(log_entry)
            
            # Update last processed record
            if events:
                self.last_record_numbers[log_type] = events[0].RecordNumber
            
            win32evtlog.CloseEventLog(hand)
            return new_logs
            
        except Exception as e:
            print(f"Error reading {log_type} log: {e}")
            return []
    
    def get_event_message(self, event):
        """Extract message from event"""
        try:
            # Try to get the formatted message
            msg = win32evtlogutil.SafeFormatMessage(event, event.SourceName)
            if msg:
                return msg.strip()[:500]  # Limit message length
        except:
            pass
        
        # Fallback to string data
        if event.StringInserts:
            return ' '.join(filter(None, event.StringInserts))[:500]
        
        return f"Event ID {event.EventID} from {event.SourceName}"
    
    def send_logs(self, logs):
        """Send logs to the API"""
        if not logs:
            return
        
        try:
            response = self.session.post(
                API_URL,
                json=logs,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Sent {len(logs)} logs to API")
            else:
                print(f"❌ Failed to send logs: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending logs: {e}")
    
    def collect_and_send(self):
        """Collect logs from all sources and send to API"""
        all_logs = []
        
        for log_type, flags in LOG_TYPES.items():
            logs = self.read_events(log_type, flags)
            all_logs.extend(logs)
        
        if all_logs:
            self.send_logs(all_logs)
        else:
            print(f"ℹ️  No new events at {datetime.now().strftime('%H:%M:%S')}")
    
    def run(self):
        """Main loop"""
        print("=" * 60)
        print("Windows Event Log Collector")
        print("=" * 60)
        print(f"Monitoring: {', '.join(LOG_TYPES.keys())}")
        print(f"Source: {SOURCE_NAME}")
        print(f"API: {API_URL}")
        print(f"Poll interval: {POLL_INTERVAL} seconds")
        print("=" * 60)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.collect_and_send()
                time.sleep(POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n✋ Stopping log collector...")
            print("Goodbye!")


if __name__ == "__main__":
    # Check if pywin32 is installed
    try:
        import win32evtlog
    except ImportError:
        print("❌ Error: pywin32 is not installed")
        print("\nInstall it with:")
        print("  pip install pywin32")
        exit(1)
    
    collector = WindowsLogCollector()
    collector.run()

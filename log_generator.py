"""
Simple Log Generator
Simulates network activity by generating random logs and sending them to the API
Useful for testing and demonstration purposes
"""

import requests
import time
import random
from datetime import datetime
import socket

# Configuration
API_URL = "http://localhost:5000/api/logs/ingest"
INTERVAL = 5  # Generate logs every 5 seconds
SOURCE_NAME = socket.gethostname()

# Sample log templates
LOG_TEMPLATES = {
    'INFO': [
        "User authentication successful",
        "Request processed successfully",
        "Health check passed",
        "Service started successfully",
        "Configuration loaded",
        "Connection established to database",
        "Cache hit for key",
        "Session created for user",
    ],
    'WARNING': [
        "High CPU usage detected: {value}%",
        "Memory usage above threshold: {value}%",
        "Slow query detected: {value}ms",
        "Connection pool nearly exhausted",
        "Disk space running low: {value}% remaining",
        "Request timeout warning",
        "Retry attempt {value} for failed operation",
    ],
    'ERROR': [
        "Connection timeout to database",
        "Failed to connect to cache server",
        "Query execution failed",
        "Authentication failed for user",
        "File not found: config.json",
        "API request failed with status {value}",
        "Failed to write to log file",
    ],
    'CRITICAL': [
        "Disk failure detected on drive {value}",
        "Database connection pool exhausted",
        "Out of memory error",
        "Service crashed unexpectedly",
        "Security breach detected",
        "Data corruption detected",
    ]
}

SOURCES = [
    "web-server-01",
    "web-server-02", 
    "database-01",
    "api-gateway",
    "load-balancer",
    "cache-server",
    "storage-server",
]


class LogGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.log_count = 0
    
    def generate_log(self):
        """Generate a random log entry"""
        # Weight towards INFO logs (70%), WARNING (20%), ERROR (8%), CRITICAL (2%)
        level = random.choices(
            ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            weights=[70, 20, 8, 2]
        )[0]
        
        # Pick random source
        source = random.choice(SOURCES)
        
        # Pick random message template
        message_template = random.choice(LOG_TEMPLATES[level])
        
        # Fill in placeholders
        message = message_template.format(
            value=random.randint(50, 99)
        )
        
        return {
            'source': source,
            'level': level,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def send_logs(self, logs):
        """Send logs to the API"""
        try:
            response = self.session.post(
                API_URL,
                json=logs,
                timeout=5
            )
            
            if response.status_code == 201:
                self.log_count += len(logs)
                print(f"✅ Sent {len(logs)} logs (Total: {self.log_count})")
                for log in logs:
                    icon = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌', 'CRITICAL': '🔴'}[log['level']]
                    print(f"   {icon} [{log['source']}] {log['message'][:60]}")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
    
    def run(self):
        """Main loop"""
        print("=" * 70)
        print("🔄 Automatic Log Generator")
        print("=" * 70)
        print(f"API: {API_URL}")
        print(f"Interval: {INTERVAL} seconds")
        print(f"Sources: {', '.join(SOURCES)}")
        print("=" * 70)
        print("\nGenerating logs... Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Generate 1-3 logs per interval
                num_logs = random.randint(1, 3)
                logs = [self.generate_log() for _ in range(num_logs)]
                
                self.send_logs(logs)
                time.sleep(INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n✋ Stopping log generator...")
            print(f"📊 Total logs generated: {self.log_count}")
            print("Goodbye!")


if __name__ == "__main__":
    generator = LogGenerator()
    generator.run()

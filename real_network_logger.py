import subprocess
import time
import requests
import socket
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:5000/api/logs/ingest"
POLL_INTERVAL = 2  # Check every 2 seconds
SOURCE_NAME = socket.gethostname()

class NetworkMonitor:
    def __init__(self):
        self.active_connections = set()
        self.session = requests.Session()
        self.log_count = 0

    def get_connections(self):
        """Get current established connections using netstat"""
        try:
            # Run netstat -n to get numerical addresses (faster)
            # -p TCP to only get TCP (usually what we care about for connections)
            output = subprocess.check_output("netstat -n -p TCP", shell=True).decode('utf-8', errors='ignore')
            lines = output.splitlines()
            connections = set()
            
            for line in lines:
                parts = line.split()
                # Expected format: Proto Local Address Foreign Address State
                if len(parts) >= 4 and parts[0] == 'TCP':
                    local = parts[1]
                    remote = parts[2]
                    state = parts[3]
                    
                    # We are interested in established connections
                    if state == 'ESTABLISHED':
                        # Create a unique identifier for the connection
                        conn_id = f"{local} <-> {remote}"
                        connections.add(conn_id)
            
            return connections
        except Exception as e:
            print(f"Error running netstat: {e}")
            return set()

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
                self.log_count += len(logs)
                print(f"✅ Sent {len(logs)} logs (Total: {self.log_count})")
                for log in logs:
                    icon = '🔌' if 'New' in log['message'] else '❌'
                    print(f"   {icon} {log['message']}")
            else:
                print(f"❌ Failed to send logs: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending logs: {e}")

    def run(self):
        print("=" * 60)
        print("🔌 Real-time Network Connection Monitor")
        print("=" * 60)
        print(f"Source: {SOURCE_NAME}")
        print(f"API: {API_URL}")
        print(f"Poll interval: {POLL_INTERVAL} seconds")
        print("=" * 60)
        print("\nMonitoring network connections... Press Ctrl+C to stop\n")
        
        # Initial scan
        self.active_connections = self.get_connections()
        print(f"ℹ️  Found {len(self.active_connections)} existing connections (not logging initial state)")
        
        try:
            while True:
                time.sleep(POLL_INTERVAL)
                current_connections = self.get_connections()
                
                new_conns = current_connections - self.active_connections
                closed_conns = self.active_connections - current_connections
                
                logs = []
                
                # Log new connections
                for conn in new_conns:
                    logs.append({
                        'source': f"{SOURCE_NAME}/Network",
                        'level': 'INFO',
                        'message': f"New connection established: {conn}",
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {
                            'type': 'connection_opened',
                            'connection': conn,
                            'monitor': 'real_network_logger'
                        }
                    })
                
                # Log closed connections
                for conn in closed_conns:
                    logs.append({
                        'source': f"{SOURCE_NAME}/Network",
                        'level': 'INFO',
                        'message': f"Connection closed: {conn}",
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {
                            'type': 'connection_closed',
                            'connection': conn,
                            'monitor': 'real_network_logger'
                        }
                    })
                
                if logs:
                    self.send_logs(logs)
                
                self.active_connections = current_connections
                
        except KeyboardInterrupt:
            print("\n\n✋ Stopping network monitor...")
            print("Goodbye!")

if __name__ == "__main__":
    monitor = NetworkMonitor()
    monitor.run()

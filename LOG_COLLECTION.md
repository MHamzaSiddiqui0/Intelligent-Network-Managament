# Automatic Log Collection

This directory contains tools to automatically send logs to the Network Management System.

## 📋 Available Tools

### 1. **real_network_logger.py** - Real-time Network Monitor (🆕 Recommended)

**What it does:**
- Monitors **REAL** network connections on your computer in real-time
- Detects new TCP connections and closed connections
- Uses `netstat` to capture live network activity
- Sends logs to the API automatically

**How to use:**
```bash
# Start the Flask server (in one terminal)
python main.py

# Run the network monitor (in another terminal)
python real_network_logger.py
```

**Output:**
```
� Real-time Network Connection Monitor
============================================================
Source: YOUR-COMPUTER
API: http://localhost:5000/api/logs/ingest
Poll interval: 2 seconds
============================================================

ℹ️  Found 45 existing connections (not logging initial state)
✅ Sent 1 logs (Total: 1)
   🔌 New connection established: 192.168.1.10:54321 <-> 142.250.1.1:443
✅ Sent 1 logs (Total: 2)
   ❌ Connection closed: 192.168.1.10:54321 <-> 142.250.1.1:443
```

---

### 2. **log_collector.py** - Windows Event Log Collector (System Logs)

**What it does:**
- Monitors Windows Event Logs (Application and System)
- Captures real errors and warnings from your computer
- Automatically sends them to the API
- Runs continuously in the background

**How to use:**
```bash
# Install dependencies
pip install pywin32 requests

# Run the log collector
python log_collector.py
```

---

### 3. **log_generator.py** - Simulated Log Generator (For Testing)

**What it does:**
- Generates **FAKE** random logs for testing purposes
- Useful if you don't have real activity to monitor

---

## 🚀 Quick Start (Real Data)

To see real-time data from your computer:

```bash
# Terminal 1: Start server
python main.py

# Terminal 2: Monitor Network Connections
python real_network_logger.py

# Terminal 3 (Optional): Monitor System Events
python log_collector.py

# Open browser: http://localhost:5000
```

---

## 📊 What Happens

1. **real_network_logger.py** runs `netstat` every 2 seconds.
2. It compares current connections with the previous state.
3. If a connection opens or closes, it sends a log to the API.
4. **log_collector.py** listens for Windows Event Logs.
5. All logs are stored in the database and visible on the dashboard.

---

## ⚙️ Configuration

### **real_network_logger.py:**
```python
API_URL = "http://localhost:5000/api/logs/ingest"
POLL_INTERVAL = 2  # Check every 2 seconds
```

### **log_collector.py:**
```python
API_URL = "http://localhost:5000/api/logs/ingest"
POLL_INTERVAL = 10
```

---

## � Tips

- **Generate Activity**: Open a web browser and visit some sites to see "New connection" logs appear in `real_network_logger.py`.
- **System Events**: To see logs from `log_collector.py`, you might need to wait for a real system event or trigger one (e.g., by restarting a service).

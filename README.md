# Intelligent Network Management System

A comprehensive Flask-based network management platform with three core modules:
1. **Network Log Summarization** - Analyzes and condenses network logs
2. **Automated Alert Classification** - Categorizes and prioritizes alerts
3. **ChatOps Troubleshooting Assistant** - Command-line interface for network management

## Features

### 📊 Network Log Summarization
- Bulk log ingestion and storage
- Statistical analysis and anomaly detection
- Time-based log aggregation
- Automatic summary generation with key events

### 🚨 Automated Alert Classification
- Pattern-based alert classification
- Priority scoring and severity assignment
- Duplicate detection and alert grouping
- Customizable classification rules

### 💬 ChatOps Assistant
- 14+ built-in commands for monitoring and troubleshooting
- Natural language query support
- Real-time system status and health checks
- Network diagnostics (ping, traceroute)
- Comprehensive reporting

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python init_db.py
   ```

3. **Start the application:**
   ```bash
   python main.py
   ```

4. **Access the dashboard:**
   Open http://localhost:5000 in your browser

## Project Structure

```
cn project/
├── main.py                 # Flask application entry point
├── config.py              # Application configuration
├── models.py              # Database models
├── init_db.py             # Database initialization script
├── requirements.txt       # Python dependencies
├── routes/
│   ├── logs.py           # Log management API
│   ├── alerts.py         # Alert management API
│   └── chat.py           # ChatOps API
├── services/
│   ├── log_summarizer.py # Log summarization engine
│   ├── alert_classifier.py # Alert classification engine
│   └── chatops.py        # ChatOps command processor
├── templates/
│   └── index.html        # Main dashboard
└── static/
    ├── css/
    │   └── style.css     # Dashboard styles
    └── js/
        └── app.js        # Frontend JavaScript

## API Endpoints

### Logs
- `POST /api/logs/ingest` - Ingest network logs
- `POST /api/logs/summarize` - Generate log summary
- `GET /api/logs/summaries` - Retrieve summaries
- `GET /api/logs/raw` - Query raw logs
- `GET /api/logs/stats` - Get log statistics

### Alerts
- `POST /api/alerts/ingest` - Ingest new alert
- `GET /api/alerts` - List alerts (with filtering)
- `PUT /api/alerts/<id>/status` - Update alert status
- `POST /api/alerts/rules` - Create classification rule
- `GET /api/alerts/rules` - List rules
- `GET /api/alerts/stats` - Get alert statistics
- `GET /api/alerts/groups` - Get grouped alerts

### ChatOps
- `POST /api/chat/message` - Send command
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/commands` - List available commands

## ChatOps Commands

**Monitoring:**
- `status` - System status overview
- `health` - Health check
- `metrics [hours]` - Network metrics

**Logs:**
- `logs [level]` - View recent logs
- `errors` - View recent errors
- `recent [minutes]` - Recent activity

**Alerts:**
- `alerts [status]` - View alerts
- `critical` - View critical alerts
- `acknowledge <id>` - Acknowledge alert

**Diagnostics:**
- `ping <host>` - Ping a host
- `summarize [hours]` - Log summary
- `report` - Comprehensive report

## Technologies

- **Backend:** Python 3, Flask, SQLAlchemy
- **Database:** SQLite (easily switchable to MySQL)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Custom CSS with glassmorphism and dark theme

## Course Project Notes

This project demonstrates:
- REST API design and implementation
- Database modeling and ORM usage
- Real-time data processing and analysis
- Pattern matching and rule-based systems
- Web dashboard development
- Anomaly detection algorithms
- Statistical analysis of network data
- Command-line interface design

Perfect for a Computer Networks course project showcasing network management, log analysis, and automated monitoring systems.

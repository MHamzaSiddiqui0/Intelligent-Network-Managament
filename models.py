from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class NetworkLog(db.Model):
    """Stores raw network logs"""
    __tablename__ = 'network_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = db.Column(db.String(100), nullable=False, index=True)
    level = db.Column(db.String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = db.Column(db.Text, nullable=False)
    meta_data = db.Column(db.Text)  # JSON string for additional data
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'level': self.level,
            'message': self.message,
            'metadata': json.loads(self.meta_data) if self.meta_data else {}
        }


class LogSummary(db.Model):
    """Stores generated log summaries"""
    __tablename__ = 'log_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False, index=True)
    total_logs = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    warning_count = db.Column(db.Integer, default=0)
    summary_text = db.Column(db.Text)
    key_events = db.Column(db.Text)  # JSON array of important events
    anomalies = db.Column(db.Text)  # JSON array of detected anomalies
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_logs': self.total_logs,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'summary_text': self.summary_text,
            'key_events': json.loads(self.key_events) if self.key_events else [],
            'anomalies': json.loads(self.anomalies) if self.anomalies else [],
            'created_at': self.created_at.isoformat()
        }


class Alert(db.Model):
    """Stores network alerts"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), nullable=False, index=True)  # low, medium, high, critical
    category = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), default='open', index=True)  # open, acknowledged, resolved
    priority_score = db.Column(db.Float, default=0.5)
    source = db.Column(db.String(100))
    meta_data = db.Column(db.Text)  # JSON string
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'category': self.category,
            'status': self.status,
            'priority_score': self.priority_score,
            'source': self.source,
            'metadata': json.loads(self.meta_data) if self.meta_data else {},
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertRule(db.Model):
    """Stores alert classification rules"""
    __tablename__ = 'alert_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    pattern = db.Column(db.String(500), nullable=False)  # Regex or keyword pattern
    category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    priority_boost = db.Column(db.Float, default=0.0)  # Adjustment to priority score
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'pattern': self.pattern,
            'category': self.category,
            'severity': self.severity,
            'priority_boost': self.priority_boost,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat()
        }


class ChatMessage(db.Model):
    """Stores chat interactions"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text)
    command_type = db.Column(db.String(50))  # status, logs, alerts, diagnostic, etc.
    execution_time = db.Column(db.Float)  # seconds
    success = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'command_type': self.command_type,
            'execution_time': self.execution_time,
            'success': self.success
        }


class NetworkMetric(db.Model):
    """Stores network performance metrics"""
    __tablename__ = 'network_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    source = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'unit': self.unit,
            'source': self.source
        }

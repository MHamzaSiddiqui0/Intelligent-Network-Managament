import re
from datetime import datetime
from collections import Counter
from models import Alert, AlertRule, db
import json


class AlertClassifier:
    """Service for classifying and prioritizing network alerts"""
    
    def __init__(self, auto_ack_threshold=0.3):
        self.auto_ack_threshold = auto_ack_threshold
        self.severity_scores = {
            'low': 0.25,
            'medium': 0.5,
            'high': 0.75,
            'critical': 1.0
        }
    
    def classify_alert(self, alert_data):
        """Classify an incoming alert and assign priority"""
        
        # Extract alert information
        title = alert_data.get('title', '')
        description = alert_data.get('description', '')
        combined_text = f"{title} {description}".lower()
        
        # Get all active rules
        rules = AlertRule.query.filter_by(enabled=True).all()
        
        # Apply classification rules
        matched_rules = []
        for rule in rules:
            if self._matches_pattern(combined_text, rule.pattern):
                matched_rules.append(rule)
        
        # Determine category and severity
        if matched_rules:
            # Use the highest priority matched rule
            best_rule = max(matched_rules, key=lambda r: self.severity_scores.get(r.severity, 0))
            category = best_rule.category
            severity = best_rule.severity
            priority_boost = best_rule.priority_boost
        else:
            # Default classification based on keywords
            category = self._classify_category(combined_text)
            severity = self._classify_severity(combined_text)
            priority_boost = 0
        
        # Calculate priority score
        base_score = self.severity_scores.get(severity, 0.5)
        priority_score = min(1.0, base_score + priority_boost)
        
        # Determine initial status
        status = 'open'
        if priority_score < self.auto_ack_threshold:
            status = 'acknowledged'
        
        # Create alert
        alert = Alert(
            timestamp=datetime.fromisoformat(alert_data['timestamp']) if 'timestamp' in alert_data else datetime.utcnow(),
            title=title,
            description=description,
            severity=severity,
            category=category,
            status=status,
            priority_score=priority_score,
            source=alert_data.get('source', 'unknown'),
            meta_data=json.dumps(alert_data.get('metadata', {})),
            acknowledged_at=datetime.utcnow() if status == 'acknowledged' else None
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert
    
    def _matches_pattern(self, text, pattern):
        """Check if text matches a pattern (regex or keyword)"""
        try:
            # Try as regex first
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            # Fall back to simple keyword matching
            return pattern.lower() in text
    
    def _classify_category(self, text):
        """Classify alert category based on keywords"""
        category_keywords = {
            'security': ['security', 'breach', 'unauthorized', 'attack', 'intrusion', 'malware', 'virus'],
            'network': ['network', 'connection', 'packet', 'bandwidth', 'latency', 'timeout', 'dns'],
            'performance': ['performance', 'slow', 'high cpu', 'memory', 'disk', 'load', 'throughput'],
            'system': ['system', 'service', 'daemon', 'process', 'kernel', 'boot', 'shutdown'],
            'application': ['application', 'app', 'database', 'query', 'api', 'request']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'system'  # Default category
    
    def _classify_severity(self, text):
        """Classify alert severity based on keywords"""
        if any(word in text for word in ['critical', 'emergency', 'down', 'failed', 'breach']):
            return 'critical'
        elif any(word in text for word in ['error', 'failure', 'high', 'warning']):
            return 'high'
        elif any(word in text for word in ['warning', 'degraded', 'slow']):
            return 'medium'
        else:
            return 'low'
    
    def get_alerts(self, filters=None):
        """Get alerts with optional filtering"""
        query = Alert.query
        
        if filters:
            if 'severity' in filters:
                query = query.filter(Alert.severity == filters['severity'])
            if 'category' in filters:
                query = query.filter(Alert.category == filters['category'])
            if 'status' in filters:
                query = query.filter(Alert.status == filters['status'])
            if 'min_priority' in filters:
                query = query.filter(Alert.priority_score >= filters['min_priority'])
        
        return query.order_by(Alert.priority_score.desc(), Alert.timestamp.desc()).all()
    
    def update_alert_status(self, alert_id, new_status):
        """Update an alert's status"""
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return None
        
        alert.status = new_status
        
        if new_status == 'acknowledged' and not alert.acknowledged_at:
            alert.acknowledged_at = datetime.utcnow()
        elif new_status == 'resolved':
            alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        return alert
    
    def group_similar_alerts(self, time_window_hours=1):
        """Group similar alerts that occurred within a time window"""
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_alerts = Alert.query.filter(Alert.timestamp >= cutoff_time).all()
        
        # Group by title similarity
        groups = {}
        for alert in recent_alerts:
            # Simple grouping by first 50 characters of title
            key = alert.title[:50]
            if key not in groups:
                groups[key] = []
            groups[key].append(alert)
        
        # Return groups with more than one alert
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def create_rule(self, name, pattern, category, severity, priority_boost=0.0):
        """Create a new classification rule"""
        rule = AlertRule(
            name=name,
            pattern=pattern,
            category=category,
            severity=severity,
            priority_boost=priority_boost
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return rule
    
    def get_rules(self):
        """Get all classification rules"""
        return AlertRule.query.all()

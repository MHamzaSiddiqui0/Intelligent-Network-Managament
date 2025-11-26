from datetime import datetime, timedelta
from collections import Counter, defaultdict
from models import NetworkLog, LogSummary, db
import json
import re
from statistics import mean, stdev


class LogSummarizer:
    """Service for summarizing network logs"""
    
    def __init__(self, anomaly_threshold=2.5, max_events=10):
        self.anomaly_threshold = anomaly_threshold
        self.max_events = max_events
    
    def generate_summary(self, start_time, end_time):
        """Generate a summary for logs within the given time range"""
        
        # Fetch logs in the time range
        logs = NetworkLog.query.filter(
            NetworkLog.timestamp >= start_time,
            NetworkLog.timestamp <= end_time
        ).all()
        
        if not logs:
            return None
        
        # Statistical analysis
        total_logs = len(logs)
        level_counts = Counter(log.level for log in logs)
        source_counts = Counter(log.source for log in logs)
        
        # Extract key events
        key_events = self._extract_key_events(logs)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(logs, start_time, end_time)
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            total_logs, level_counts, source_counts, key_events, anomalies
        )
        
        # Create and save summary
        summary = LogSummary(
            start_time=start_time,
            end_time=end_time,
            total_logs=total_logs,
            error_count=level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0),
            warning_count=level_counts.get('WARNING', 0),
            summary_text=summary_text,
            key_events=json.dumps(key_events),
            anomalies=json.dumps(anomalies)
        )
        
        db.session.add(summary)
        db.session.commit()
        
        return summary
    
    def _extract_key_events(self, logs):
        """Extract the most important events from logs"""
        key_events = []
        
        # Prioritize by severity
        severity_order = {'CRITICAL': 4, 'ERROR': 3, 'WARNING': 2, 'INFO': 1}
        
        # Sort logs by severity and timestamp
        sorted_logs = sorted(
            logs,
            key=lambda x: (severity_order.get(x.level, 0), x.timestamp),
            reverse=True
        )
        
        # Get top events
        for log in sorted_logs[:self.max_events]:
            key_events.append({
                'timestamp': log.timestamp.isoformat(),
                'level': log.level,
                'source': log.source,
                'message': log.message[:200]  # Truncate long messages
            })
        
        return key_events
    
    def _detect_anomalies(self, logs, start_time, end_time):
        """Detect anomalies in log patterns"""
        anomalies = []
        
        # Time-based analysis: Count logs per hour
        time_buckets = defaultdict(int)
        duration = (end_time - start_time).total_seconds() / 3600
        
        for log in logs:
            hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
            time_buckets[hour] += 1
        
        if len(time_buckets) > 1:
            counts = list(time_buckets.values())
            avg_count = mean(counts)
            
            if len(counts) > 2:
                std_count = stdev(counts)
                
                # Find time periods with unusual activity
                for hour, count in time_buckets.items():
                    if std_count > 0 and abs(count - avg_count) > self.anomaly_threshold * std_count:
                        anomalies.append({
                            'type': 'activity_spike' if count > avg_count else 'activity_drop',
                            'timestamp': hour.isoformat(),
                            'value': count,
                            'expected': round(avg_count, 2),
                            'description': f"Unusual {'spike' if count > avg_count else 'drop'} in log activity"
                        })
        
        # Error rate analysis
        error_logs = [log for log in logs if log.level in ['ERROR', 'CRITICAL']]
        if error_logs:
            error_rate = len(error_logs) / len(logs)
            if error_rate > 0.1:  # More than 10% errors
                anomalies.append({
                    'type': 'high_error_rate',
                    'value': round(error_rate * 100, 2),
                    'description': f"High error rate detected: {round(error_rate * 100, 2)}%"
                })
        
        # Source-based anomalies
        source_counts = Counter(log.source for log in logs)
        if source_counts:
            max_source_count = max(source_counts.values())
            for source, count in source_counts.items():
                if count > max_source_count * 0.5 and count > 10:
                    error_count = sum(1 for log in logs if log.source == source and log.level in ['ERROR', 'CRITICAL'])
                    if error_count / count > 0.2:
                        anomalies.append({
                            'type': 'source_errors',
                            'source': source,
                            'error_count': error_count,
                            'total_count': count,
                            'description': f"High error rate from source: {source}"
                        })
        
        return anomalies[:5]  # Return top 5 anomalies
    
    def _generate_summary_text(self, total_logs, level_counts, source_counts, key_events, anomalies):
        """Generate human-readable summary text"""
        lines = []
        
        # Overall statistics
        lines.append(f"Total logs processed: {total_logs}")
        
        # Level breakdown
        level_parts = []
        for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
            count = level_counts.get(level, 0)
            if count > 0:
                level_parts.append(f"{count} {level}")
        lines.append(f"Breakdown: {', '.join(level_parts)}")
        
        # Top sources
        top_sources = source_counts.most_common(3)
        if top_sources:
            source_str = ', '.join(f"{source} ({count})" for source, count in top_sources)
            lines.append(f"Top sources: {source_str}")
        
        # Anomalies
        if anomalies:
            lines.append(f"⚠ {len(anomalies)} anomalies detected")
            for anomaly in anomalies[:3]:
                lines.append(f"  - {anomaly['description']}")
        
        # Key events
        critical_count = sum(1 for event in key_events if event['level'] == 'CRITICAL')
        error_count = sum(1 for event in key_events if event['level'] == 'ERROR')
        if critical_count > 0:
            lines.append(f"🔴 {critical_count} critical events require immediate attention")
        elif error_count > 0:
            lines.append(f"⚠ {error_count} errors detected")
        
        return '\n'.join(lines)
    
    def get_recent_summaries(self, limit=10):
        """Get the most recent log summaries"""
        return LogSummary.query.order_by(LogSummary.created_at.desc()).limit(limit).all()

from datetime import datetime, timedelta
import random
from main import app
from models import db, NetworkLog, Alert, AlertRule, NetworkMetric
import json


def init_database():
    """Initialize database with tables and sample data"""
    
    with app.app_context():
        # Create all tables
        print("[*] Creating database tables...")
        db.create_all()
        print("[OK] Tables created successfully\n")
        
        # Check if data already exists
        if NetworkLog.query.first():
            print("[INFO] Database already contains data. Skipping sample data generation.")
            return
        
        # Generate sample data
        print("[*] Generating sample data...\n")
        
        # 1. Create Alert Classification Rules
        print("[*] Creating alert classification rules...")
        rules = [
            AlertRule(
                name="Critical Security Alert",
                pattern=r"(breach|intrusion|unauthorized access|malware)",
                category="security",
                severity="critical",
                priority_boost=0.3
            ),
            AlertRule(
                name="Network Timeout",
                pattern=r"(timeout|connection.*failed|network.*down)",
                category="network",
                severity="high",
                priority_boost=0.2
            ),
            AlertRule(
                name="High CPU Usage",
                pattern=r"(cpu.*high|cpu.*\d{2,3}%)",
                category="performance",
                severity="medium",
                priority_boost=0.1
            ),
            AlertRule(
                name="Service Degradation",
                pattern=r"(slow|degraded|performance.*issue)",
                category="performance",
                severity="medium",
                priority_boost=0.05
            ),
            AlertRule(
                name="Information Notice",
                pattern=r"(info|notice|update)",
                category="system",
                severity="low",
                priority_boost=0.0
            )
        ]
        
        for rule in rules:
            db.session.add(rule)
        db.session.commit()
        print(f"[OK] Created {len(rules)} classification rules\n")
        
        # 2. Generate Network Logs
        print("[*] Generating network logs...")
        sources = [
            "router-01", "router-02", "switch-main", "firewall-01",
            "server-web", "server-db", "server-app", "dns-server"
        ]
        
        log_templates = {
            'INFO': [
                "Connection established from {}",
                "Service health check passed",
                "Configuration updated successfully",
                "Backup completed: {} MB",
                "User authentication successful"
            ],
            'WARNING': [
                "High memory usage detected: {}%",
                "Response time degraded: {}ms",
                "Retry attempt {} for failed connection",
                "Certificate expires in {} days",
                "Disk usage at {}%"
            ],
            'ERROR': [
                "Connection timeout to {}",
                "Failed to resolve DNS query for {}",
                "Database query timeout after {}s",
                "API request failed with status {}",
                "Service {} not responding"
            ],
            'CRITICAL': [
                "Security breach attempt detected from {}",
                "Service {} crashed unexpectedly",
                "Disk space critically low: {} GB remaining",
                "Network interface {} is down",
                "Authentication server unreachable"
            ]
        }
        
        base_time = datetime.utcnow() - timedelta(hours=6)
        log_count = 0
        
        for hour in range(6):
            hour_time = base_time + timedelta(hours=hour)
            logs_per_hour = random.randint(80, 150)
            
            for _ in range(logs_per_hour):
                minute_offset = random.randint(0, 59)
                timestamp = hour_time + timedelta(minutes=minute_offset)
                
                # Weighted distribution of log levels
                level = random.choices(
                    ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    weights=[0.6, 0.25, 0.12, 0.03]
                )[0]
                
                source = random.choice(sources)
                template = random.choice(log_templates[level])
                
                # Fill in template placeholders
                if '{}' in template:
                    if 'from' in template or 'to' in template:
                        message = template.format(f"192.168.{random.randint(1,255)}.{random.randint(1,255)}")
                    elif 'MB' in template or 'GB' in template:
                        message = template.format(random.randint(100, 5000))
                    elif '%' in template:
                        message = template.format(random.randint(70, 98))
                    elif 'ms' in template:
                        message = template.format(random.randint(500, 3000))
                    elif 's' in template:
                        message = template.format(random.randint(5, 30))
                    elif 'days' in template:
                        message = template.format(random.randint(1, 30))
                    elif 'status' in template:
                        message = template.format(random.choice([400, 403, 404, 500, 502, 503]))
                    elif 'Retry' in template:
                        message = template.format(random.randint(1, 5))
                    else:
                        message = template.format(source)
                else:
                    message = template
                
                log = NetworkLog(
                    timestamp=timestamp,
                    source=source,
                    level=level,
                    message=message,
                    meta_data=json.dumps({
                        'environment': 'production',
                        'region': 'us-east-1'
                    })
                )
                db.session.add(log)
                log_count += 1
        
        db.session.commit()
        print(f"[OK] Generated {log_count} network logs\n")
        
        # 3. Generate Alerts
        print("[*] Generating alerts...")
        alert_templates = [
            {
                'title': 'High CPU Usage on server-web',
                'description': 'CPU usage exceeded 85% threshold for over 10 minutes',
                'category': 'performance',
                'severity': 'medium'
            },
            {
                'title': 'Network timeout detected',
                'description': 'Multiple connection timeouts to external API endpoint',
                'category': 'network',
                'severity': 'high'
            },
            {
                'title': 'Suspicious login attempts',
                'description': 'Multiple failed authentication attempts from unknown IP',
                'category': 'security',
                'severity': 'critical'
            },
            {
                'title': 'Database query performance degraded',
                'description': 'Average query response time increased by 250%',
                'category': 'performance',
                'severity': 'medium'
            },
            {
                'title': 'SSL certificate expiring soon',
                'description': 'SSL certificate for api.example.com expires in 7 days',
                'category': 'system',
                'severity': 'medium'
            },
            {
                'title': 'Backup job failed',
                'description': 'Automated backup job failed with error code 503',
                'category': 'system',
                'severity': 'high'
            },
            {
                'title': 'Memory leak detected',
                'description': 'Application memory usage growing continuously',
                'category': 'performance',
                'severity': 'high'
            },
            {
                'title': 'DDoS attack suspected',
                'description': 'Unusual spike in traffic from multiple sources',
                'category': 'security',
                'severity': 'critical'
            },
            {
                'title': 'Service health check failing',
                'description': 'Health check endpoint returning 503 errors',
                'category': 'application',
                'severity': 'high'
            },
            {
                'title': 'Disk space low',
                'description': 'Available disk space below 10% on /data volume',
                'category': 'system',
                'severity': 'medium'
            }
        ]
        
        alert_count = 0
        base_alert_time = datetime.utcnow() - timedelta(hours=3)
        
        for i, template in enumerate(alert_templates):
            timestamp = base_alert_time + timedelta(minutes=i * 15)
            
            # Assign severity scores
            severity_scores = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
            priority_score = severity_scores[template['severity']] + random.uniform(-0.1, 0.1)
            priority_score = max(0, min(1, priority_score))
            
            # Random status
            status = random.choices(
                ['open', 'acknowledged', 'resolved'],
                weights=[0.4, 0.3, 0.3]
            )[0]
            
            alert = Alert(
                timestamp=timestamp,
                title=template['title'],
                description=template['description'],
                severity=template['severity'],
                category=template['category'],
                status=status,
                priority_score=priority_score,
                source=random.choice(sources),
                meta_data=json.dumps({'auto_generated': True}),
                acknowledged_at=timestamp + timedelta(minutes=random.randint(5, 30)) if status in ['acknowledged', 'resolved'] else None,
                resolved_at=timestamp + timedelta(hours=random.randint(1, 3)) if status == 'resolved' else None
            )
            db.session.add(alert)
            alert_count += 1
        
        db.session.commit()
        print(f"[OK] Generated {alert_count} alerts\n")
        
        # 4. Generate Network Metrics
        print("[*] Generating network metrics...")
        metric_names = [
            ('cpu_usage', '%'),
            ('memory_usage', '%'),
            ('network_throughput', 'Mbps'),
            ('response_time', 'ms'),
            ('error_rate', '%')
        ]
        
        metric_count = 0
        base_metric_time = datetime.utcnow() - timedelta(hours=6)
        
        for hour in range(6):
            for minute in range(0, 60, 5):  # Every 5 minutes
                timestamp = base_metric_time + timedelta(hours=hour, minutes=minute)
                
                for metric_name, unit in metric_names:
                    # Generate realistic values with some variation
                    if metric_name == 'cpu_usage':
                        value = random.uniform(20, 80)
                    elif metric_name == 'memory_usage':
                        value = random.uniform(40, 85)
                    elif metric_name == 'network_throughput':
                        value = random.uniform(100, 800)
                    elif metric_name == 'response_time':
                        value = random.uniform(50, 300)
                    elif metric_name == 'error_rate':
                        value = random.uniform(0.1, 5)
                    
                    metric = NetworkMetric(
                        timestamp=timestamp,
                        metric_name=metric_name,
                        metric_value=round(value, 2),
                        unit=unit,
                        source=random.choice(sources)
                    )
                    db.session.add(metric)
                    metric_count += 1
        
        db.session.commit()
        print(f"[OK] Generated {metric_count} metrics\n")
        
        print("=" * 50)
        print("[SUCCESS] Database initialization complete!")
        print("=" * 50)
        print("\nSummary:")
        print(f"  - Classification Rules: {len(rules)}")
        print(f"  - Network Logs: {log_count}")
        print(f"  - Alerts: {alert_count}")
        print(f"  - Metrics: {metric_count}")
        print("\nYou can now start the application with: python main.py")


if __name__ == '__main__':
    init_database()

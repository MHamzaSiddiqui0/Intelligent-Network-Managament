import re
import subprocess
import platform
from datetime import datetime, timedelta
from models import ChatMessage, NetworkLog, Alert, LogSummary, NetworkMetric, db
from collections import Counter


class ChatOps:
    """ChatOps service for network troubleshooting and management"""
    
    def __init__(self):
        self.commands = {
            'status': self._cmd_status,
            'health': self._cmd_health,
            'metrics': self._cmd_metrics,
            'logs': self._cmd_logs,
            'errors': self._cmd_errors,
            'recent': self._cmd_recent,
            'alerts': self._cmd_alerts,
            'critical': self._cmd_critical,
            'acknowledge': self._cmd_acknowledge,
            'ping': self._cmd_ping,
            'traceroute': self._cmd_traceroute,
            'check': self._cmd_check,
            'summarize': self._cmd_summarize,
            'report': self._cmd_report,
            'help': self._cmd_help
        }
    
    def process_message(self, user_message):
        """Process a user message and return a bot response"""
        start_time = datetime.utcnow()
        
        # Parse command
        command, args = self._parse_command(user_message)
        
        # Execute command
        if command in self.commands:
            try:
                response = self.commands[command](args)
                success = True
            except Exception as e:
                response = f"❌ Error executing command: {str(e)}"
                success = False
        else:
            # Try natural language understanding
            response = self._handle_natural_language(user_message)
            command = 'natural'
            success = True
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Save chat message
        chat_msg = ChatMessage(
            user_message=user_message,
            bot_response=response,
            command_type=command,
            execution_time=execution_time,
            success=success
        )
        db.session.add(chat_msg)
        db.session.commit()
        
        return response
    
    def _parse_command(self, message):
        """Parse user message into command and arguments"""
        parts = message.strip().split()
        if not parts:
            return 'help', []
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    # Command implementations
    
    def _cmd_status(self, args):
        """Get system status"""
        # Count recent logs and alerts
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        log_count = NetworkLog.query.filter(NetworkLog.timestamp >= one_hour_ago).count()
        alert_count = Alert.query.filter(Alert.timestamp >= one_hour_ago).count()
        open_alerts = Alert.query.filter(Alert.status == 'open').count()
        critical_alerts = Alert.query.filter(
            Alert.severity == 'critical',
            Alert.status == 'open'
        ).count()
        
        response = "📊 **System Status**\n\n"
        response += f"🕐 Last Hour Activity:\n"
        response += f"  • Logs processed: {log_count}\n"
        response += f"  • New alerts: {alert_count}\n"
        response += f"  • Open alerts: {open_alerts}\n"
        
        if critical_alerts > 0:
            response += f"  • ⚠️ **Critical alerts: {critical_alerts}**\n"
        else:
            response += f"  • ✅ No critical alerts\n"
        
        return response
    
    def _cmd_health(self, args):
        """Get health check summary"""
        # Check error rates
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        logs = NetworkLog.query.filter(NetworkLog.timestamp >= one_hour_ago).all()
        
        if not logs:
            return "ℹ️ No recent logs to analyze health"
        
        error_count = sum(1 for log in logs if log.level in ['ERROR', 'CRITICAL'])
        error_rate = (error_count / len(logs)) * 100
        
        response = "💚 **Health Check**\n\n"
        
        if error_rate < 5:
            response += "✅ System is healthy\n"
        elif error_rate < 15:
            response += "⚠️ Moderate issues detected\n"
        else:
            response += "🔴 System health is degraded\n"
        
        response += f"\n📈 Metrics:\n"
        response += f"  • Total logs (1h): {len(logs)}\n"
        response += f"  • Error rate: {error_rate:.2f}%\n"
        response += f"  • Errors: {error_count}\n"
        
        return response
    
    def _cmd_metrics(self, args):
        """Get network metrics"""
        hours = 1
        if args and args[0].isdigit():
            hours = int(args[0])
        
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        metrics = NetworkMetric.query.filter(NetworkMetric.timestamp >= time_threshold).all()
        
        if not metrics:
            return f"ℹ️ No metrics data available for the last {hours} hour(s)"
        
        # Group metrics by name
        metric_groups = {}
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.metric_value)
        
        response = f"📊 **Network Metrics** (last {hours}h)\n\n"
        
        for name, values in metric_groups.items():
            avg_value = sum(values) / len(values)
            max_value = max(values)
            min_value = min(values)
            response += f"**{name}**:\n"
            response += f"  • Average: {avg_value:.2f}\n"
            response += f"  • Min: {min_value:.2f} | Max: {max_value:.2f}\n\n"
        
        return response
    
    def _cmd_logs(self, args):
        """Get filtered logs"""
        level = args[0].upper() if args else None
        limit = 10
        
        query = NetworkLog.query
        if level:
            query = query.filter(NetworkLog.level == level)
        
        logs = query.order_by(NetworkLog.timestamp.desc()).limit(limit).all()
        
        if not logs:
            return f"ℹ️ No logs found{' with level ' + level if level else ''}"
        
        response = f"📝 **Recent Logs**{' (' + level + ')' if level else ''}\n\n"
        
        for log in logs:
            timestamp = log.timestamp.strftime("%H:%M:%S")
            icon = self._get_level_icon(log.level)
            response += f"{icon} `{timestamp}` [{log.source}] {log.message[:80]}\n"
        
        return response
    
    def _cmd_errors(self, args):
        """Get recent errors"""
        limit = 10
        
        errors = NetworkLog.query.filter(
            NetworkLog.level.in_(['ERROR', 'CRITICAL'])
        ).order_by(NetworkLog.timestamp.desc()).limit(limit).all()
        
        if not errors:
            return "✅ No recent errors found"
        
        response = f"🔴 **Recent Errors** (showing {len(errors)})\n\n"
        
        for error in errors:
            timestamp = error.timestamp.strftime("%H:%M:%S")
            response += f"• `{timestamp}` [{error.source}] {error.message[:80]}\n"
        
        return response
    
    def _cmd_recent(self, args):
        """Get recent activity summary"""
        minutes = 30
        if args and args[0].isdigit():
            minutes = int(args[0])
        
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        
        logs = NetworkLog.query.filter(NetworkLog.timestamp >= time_threshold).all()
        alerts = Alert.query.filter(Alert.timestamp >= time_threshold).all()
        
        response = f"⏱️ **Recent Activity** (last {minutes} minutes)\n\n"
        response += f"📝 Logs: {len(logs)}\n"
        
        if logs:
            level_counts = Counter(log.level for log in logs)
            for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
                count = level_counts.get(level, 0)
                if count > 0:
                    response += f"  • {level}: {count}\n"
        
        response += f"\n🚨 Alerts: {len(alerts)}\n"
        
        if alerts:
            severity_counts = Counter(alert.severity for alert in alerts)
            for severity in ['critical', 'high', 'medium', 'low']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    response += f"  • {severity.capitalize()}: {count}\n"
        
        return response
    
    def _cmd_alerts(self, args):
        """Get current alerts"""
        status = args[0] if args else 'open'
        limit = 10
        
        alerts = Alert.query.filter(
            Alert.status == status
        ).order_by(Alert.priority_score.desc(), Alert.timestamp.desc()).limit(limit).all()
        
        if not alerts:
            return f"ℹ️ No {status} alerts"
        
        response = f"🚨 **{status.capitalize()} Alerts** (showing {len(alerts)})\n\n"
        
        for alert in alerts:
            icon = self._get_severity_icon(alert.severity)
            timestamp = alert.timestamp.strftime("%H:%M:%S")
            response += f"{icon} `{timestamp}` **{alert.title}**\n"
            response += f"   Category: {alert.category} | Priority: {alert.priority_score:.2f}\n"
        
        return response
    
    def _cmd_critical(self, args):
        """Get critical alerts"""
        alerts = Alert.query.filter(
            Alert.severity == 'critical',
            Alert.status == 'open'
        ).order_by(Alert.timestamp.desc()).all()
        
        if not alerts:
            return "✅ No critical alerts"
        
        response = f"🔴 **Critical Alerts** ({len(alerts)} open)\n\n"
        
        for alert in alerts:
            timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            response += f"❗ **{alert.title}**\n"
            response += f"   Time: {timestamp} | Source: {alert.source}\n"
            response += f"   {alert.description[:100]}\n\n"
        
        return response
    
    def _cmd_acknowledge(self, args):
        """Acknowledge an alert"""
        if not args or not args[0].isdigit():
            return "❌ Usage: acknowledge <alert_id>"
        
        alert_id = int(args[0])
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return f"❌ Alert {alert_id} not found"
        
        alert.status = 'acknowledged'
        alert.acknowledged_at = datetime.utcnow()
        db.session.commit()
        
        return f"✅ Alert {alert_id} acknowledged: {alert.title}"
    
    def _cmd_ping(self, args):
        """Ping a host"""
        if not args:
            return "❌ Usage: ping <host>"
        
        host = args[0]
        
        try:
            # Platform-specific ping command
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '4', host]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return f"✅ Ping to {host} successful\n```\n{result.stdout[:500]}\n```"
            else:
                return f"❌ Ping to {host} failed"
        except subprocess.TimeoutExpired:
            return f"⏱️ Ping to {host} timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _cmd_traceroute(self, args):
        """Traceroute to a host"""
        if not args:
            return "❌ Usage: traceroute <host>"
        
        host = args[0]
        
        return f"ℹ️ Traceroute to {host} would be executed here (disabled for security)"
    
    def _cmd_check(self, args):
        """Check service status"""
        if not args:
            return "❌ Usage: check <service_name>"
        
        service = args[0]
        
        # Simulated service check
        return f"ℹ️ Service check for '{service}' would be executed here"
    
    def _cmd_summarize(self, args):
        """Get log summary"""
        hours = 1
        if args and args[0].isdigit():
            hours = int(args[0])
        
        summaries = LogSummary.query.order_by(LogSummary.created_at.desc()).limit(3).all()
        
        if not summaries:
            return "ℹ️ No summaries available. Generate one with: summarize <hours>"
        
        latest = summaries[0]
        
        response = f"📊 **Latest Log Summary**\n\n"
        response += f"Time range: {latest.start_time.strftime('%H:%M')} - {latest.end_time.strftime('%H:%M')}\n\n"
        response += latest.summary_text
        
        return response
    
    def _cmd_report(self, args):
        """Get comprehensive report"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        logs = NetworkLog.query.filter(NetworkLog.timestamp >= one_hour_ago).all()
        alerts = Alert.query.filter(Alert.timestamp >= one_hour_ago).all()
        
        response = "📋 **System Report** (Last Hour)\n\n"
        
        # Logs summary
        if logs:
            level_counts = Counter(log.level for log in logs)
            response += f"**Logs**: {len(logs)} total\n"
            for level, count in level_counts.most_common():
                response += f"  • {level}: {count}\n"
        
        response += f"\n"
        
        # Alerts summary
        if alerts:
            severity_counts = Counter(alert.severity for alert in alerts)
            response += f"**Alerts**: {len(alerts)} total\n"
            for severity, count in severity_counts.most_common():
                response += f"  • {severity.capitalize()}: {count}\n"
        
        # Open issues
        open_critical = Alert.query.filter(
            Alert.severity == 'critical',
            Alert.status == 'open'
        ).count()
        
        response += f"\n**Current Issues**:\n"
        response += f"  • Open critical alerts: {open_critical}\n"
        
        return response
    
    def _cmd_help(self, args):
        """Show available commands"""
        response = "🤖 **ChatOps Commands**\n\n"
        response += "**Status & Monitoring**:\n"
        response += "  • `status` - System status overview\n"
        response += "  • `health` - Health check\n"
        response += "  • `metrics [hours]` - Network metrics\n\n"
        
        response += "**Logs**:\n"
        response += "  • `logs [level]` - View recent logs\n"
        response += "  • `errors` - View recent errors\n"
        response += "  • `recent [minutes]` - Recent activity\n\n"
        
        response += "**Alerts**:\n"
        response += "  • `alerts [status]` - View alerts\n"
        response += "  • `critical` - View critical alerts\n"
        response += "  • `acknowledge <id>` - Acknowledge alert\n\n"
        
        response += "**Diagnostics**:\n"
        response += "  • `ping <host>` - Ping a host\n"
        response += "  • `traceroute <host>` - Trace route\n"
        response += "  • `check <service>` - Check service\n\n"
        
        response += "**Reports**:\n"
        response += "  • `summarize [hours]` - Log summary\n"
        response += "  • `report` - Comprehensive report\n"
        
        return response
    
    def _handle_natural_language(self, message):
        """Handle natural language queries"""
        message_lower = message.lower()
        
        # Simple keyword matching
        if any(word in message_lower for word in ['status', 'how', "what's"]):
            return self._cmd_status([])
        elif 'error' in message_lower or 'problem' in message_lower:
            return self._cmd_errors([])
        elif 'critical' in message_lower or 'urgent' in message_lower:
            return self._cmd_critical([])
        elif 'alert' in message_lower:
            return self._cmd_alerts(['open'])
        elif 'help' in message_lower:
            return self._cmd_help([])
        else:
            return "ℹ️ I'm not sure what you mean. Type 'help' to see available commands."
    
    def _get_level_icon(self, level):
        """Get icon for log level"""
        icons = {
            'CRITICAL': '🔴',
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        return icons.get(level, '•')
    
    def _get_severity_icon(self, severity):
        """Get icon for alert severity"""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        return icons.get(severity, '•')
    
    def get_chat_history(self, limit=50):
        """Get recent chat history"""
        return ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()

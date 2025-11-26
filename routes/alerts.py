from flask import Blueprint, request, jsonify
from models import Alert, AlertRule, db
from services.alert_classifier import AlertClassifier

alerts_bp = Blueprint('alerts', __name__)
classifier = AlertClassifier()


@alerts_bp.route('/api/alerts/ingest', methods=['POST'])
def ingest_alert():
    """Receive and classify a new alert"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({'error': 'Alert title is required'}), 400
        
        # Classify and store the alert
        alert = classifier.classify_alert(data)
        
        return jsonify({
            'message': 'Alert classified and stored',
            'alert': alert.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """List alerts with optional filtering"""
    try:
        # Parse filters from query parameters
        filters = {}
        
        if request.args.get('severity'):
            filters['severity'] = request.args.get('severity')
        
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('min_priority'):
            filters['min_priority'] = float(request.args.get('min_priority'))
        
        # Get alerts
        alerts = classifier.get_alerts(filters if filters else None)
        
        limit = request.args.get('limit', 50, type=int)
        alerts = alerts[:limit]
        
        return jsonify({
            'count': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts/<int:alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id):
    """Update an alert's status"""
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        new_status = data['status']
        valid_statuses = ['open', 'acknowledged', 'resolved']
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        alert = classifier.update_alert_status(alert_id, new_status)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        return jsonify({
            'message': 'Alert status updated',
            'alert': alert.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        from collections import Counter
        
        alerts = Alert.query.all()
        
        severity_counts = Counter(alert.severity for alert in alerts)
        category_counts = Counter(alert.category for alert in alerts)
        status_counts = Counter(alert.status for alert in alerts)
        
        return jsonify({
            'total_alerts': len(alerts),
            'by_severity': dict(severity_counts),
            'by_category': dict(category_counts),
            'by_status': dict(status_counts),
            'critical_open': sum(1 for a in alerts if a.severity == 'critical' and a.status == 'open')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts/rules', methods=['POST'])
def create_rule():
    """Create a new classification rule"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'pattern', 'category', 'severity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400
        
        rule = classifier.create_rule(
            name=data['name'],
            pattern=data['pattern'],
            category=data['category'],
            severity=data['severity'],
            priority_boost=data.get('priority_boost', 0.0)
        )
        
        return jsonify({
            'message': 'Rule created successfully',
            'rule': rule.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts/rules', methods=['GET'])
def get_rules():
    """List all classification rules"""
    try:
        rules = classifier.get_rules()
        
        return jsonify({
            'count': len(rules),
            'rules': [rule.to_dict() for rule in rules]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/alerts/groups', methods=['GET'])
def get_alert_groups():
    """Get grouped similar alerts"""
    try:
        hours = request.args.get('hours', 1, type=int)
        groups = classifier.group_similar_alerts(hours)
        
        result = {}
        for key, alerts in groups.items():
            result[key] = {
                'count': len(alerts),
                'alerts': [alert.to_dict() for alert in alerts]
            }
        
        return jsonify({
            'group_count': len(result),
            'groups': result
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

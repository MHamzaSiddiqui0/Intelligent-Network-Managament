from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import NetworkLog, LogSummary, db
from services.log_summarizer import LogSummarizer
import json

logs_bp = Blueprint('logs', __name__)
summarizer = LogSummarizer()


@logs_bp.route('/api/logs/ingest', methods=['POST'])
def ingest_logs():
    """Bulk log ingestion endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Support both single log and batch
        logs_data = data if isinstance(data, list) else [data]
        
        added_logs = []
        for log_data in logs_data:
            log = NetworkLog(
                timestamp=datetime.fromisoformat(log_data['timestamp']) if 'timestamp' in log_data else datetime.utcnow(),
                source=log_data.get('source', 'unknown'),
                level=log_data.get('level', 'INFO').upper(),
                message=log_data.get('message', ''),
                meta_data=json.dumps(log_data.get('metadata', {}))
            )
            db.session.add(log)
            added_logs.append(log)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully ingested {len(added_logs)} logs',
            'count': len(added_logs)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/api/logs/summarize', methods=['POST'])
def create_summary():
    """Generate a summary for a specified time range"""
    try:
        data = request.get_json()
        
        # Parse time range
        if 'start_time' in data and 'end_time' in data:
            start_time = datetime.fromisoformat(data['start_time'])
            end_time = datetime.fromisoformat(data['end_time'])
        elif 'hours' in data:
            hours = int(data['hours'])
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
        else:
            # Default to last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
        
        # Generate summary
        summary = summarizer.generate_summary(start_time, end_time)
        
        if not summary:
            return jsonify({'message': 'No logs found in the specified time range'}), 404
        
        return jsonify(summary.to_dict()), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/api/logs/summaries', methods=['GET'])
def get_summaries():
    """Retrieve log summaries"""
    try:
        limit = request.args.get('limit', 10, type=int)
        summaries = summarizer.get_recent_summaries(limit)
        
        return jsonify([summary.to_dict() for summary in summaries]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/api/logs/raw', methods=['GET'])
def get_raw_logs():
    """Query raw logs with filtering"""
    try:
        # Parse query parameters
        limit = request.args.get('limit', 100, type=int)
        level = request.args.get('level')
        source = request.args.get('source')
        hours = request.args.get('hours', type=int)
        
        # Build query
        query = NetworkLog.query
        
        if level:
            query = query.filter(NetworkLog.level == level.upper())
        
        if source:
            query = query.filter(NetworkLog.source == source)
        
        if hours:
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(NetworkLog.timestamp >= time_threshold)
        
        # Execute query
        logs = query.order_by(NetworkLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'count': len(logs),
            'logs': [log.to_dict() for log in logs]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/api/logs/stats', methods=['GET'])
def get_log_stats():
    """Get log statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        logs = NetworkLog.query.filter(NetworkLog.timestamp >= time_threshold).all()
        
        if not logs:
            return jsonify({'message': 'No logs found'}), 404
        
        # Calculate statistics
        from collections import Counter
        level_counts = Counter(log.level for log in logs)
        source_counts = Counter(log.source for log in logs)
        
        return jsonify({
            'total_logs': len(logs),
            'time_range_hours': hours,
            'level_distribution': dict(level_counts),
            'top_sources': dict(source_counts.most_common(10))
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

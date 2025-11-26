from flask import Blueprint, request, jsonify
from models import ChatMessage
from services.chatops import ChatOps

chat_bp = Blueprint('chat', __name__)
chatops = ChatOps()


@chat_bp.route('/api/chat/message', methods=['POST'])
def send_message():
    """Send a command or query to ChatOps"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        
        # Process the message
        bot_response = chatops.process_message(user_message)
        
        return jsonify({
            'user_message': user_message,
            'bot_response': bot_response
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/history', methods=['GET'])
def get_history():
    """Retrieve chat history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        messages = chatops.get_chat_history(limit)
        
        return jsonify({
            'count': len(messages),
            'messages': [msg.to_dict() for msg in messages]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/api/chat/commands', methods=['GET'])
def get_commands():
    """List available commands"""
    try:
        commands = {
            'status': {
                'description': 'Get system status overview',
                'usage': 'status',
                'category': 'monitoring'
            },
            'health': {
                'description': 'Perform health check',
                'usage': 'health',
                'category': 'monitoring'
            },
            'metrics': {
                'description': 'View network metrics',
                'usage': 'metrics [hours]',
                'category': 'monitoring'
            },
            'logs': {
                'description': 'View recent logs',
                'usage': 'logs [level]',
                'category': 'logs'
            },
            'errors': {
                'description': 'View recent errors',
                'usage': 'errors',
                'category': 'logs'
            },
            'recent': {
                'description': 'View recent activity',
                'usage': 'recent [minutes]',
                'category': 'logs'
            },
            'alerts': {
                'description': 'View alerts',
                'usage': 'alerts [status]',
                'category': 'alerts'
            },
            'critical': {
                'description': 'View critical alerts',
                'usage': 'critical',
                'category': 'alerts'
            },
            'acknowledge': {
                'description': 'Acknowledge an alert',
                'usage': 'acknowledge <alert_id>',
                'category': 'alerts'
            },
            'ping': {
                'description': 'Ping a host',
                'usage': 'ping <host>',
                'category': 'diagnostics'
            },
            'summarize': {
                'description': 'Get log summary',
                'usage': 'summarize [hours]',
                'category': 'reports'
            },
            'report': {
                'description': 'Get comprehensive report',
                'usage': 'report',
                'category': 'reports'
            },
            'help': {
                'description': 'Show available commands',
                'usage': 'help',
                'category': 'help'
            }
        }
        
        return jsonify(commands), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

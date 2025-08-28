from flask import Blueprint, request, jsonify
from models import InteractionLog, db

logging_bp = Blueprint('logging', __name__)

@logging_bp.route('/api/logs/backend', methods=['GET'])
def get_backend_logs():
    logs = InteractionLog.query.filter_by(source='backend').all()
    return jsonify([{
        'id': log.id,
        'action': log.action,
        'description': log.description,
        'timestamp': log.timestamp.isoformat()
    } for log in logs]), 200

@logging_bp.route('/api/logs/frontend', methods=['GET'])
def get_frontend_logs():
    logs = InteractionLog.query.filter_by(source='frontend').all()
    return jsonify([{
        'id': log.id,
        'action': log.action,
        'description': log.description,
        'timestamp': log.timestamp.isoformat()
    } for log in logs]), 200

@logging_bp.route('/api/logs/frontend', methods=['POST'])
def log_frontend_interaction():
    data = request.get_json()
    log = InteractionLog(
        action=data.get('action'),
        description=data.get('description'),
        source='frontend'
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Log recorded successfully'}), 201

@logging_bp.route('/api/logs/backend', methods=['POST'])
def log_backend_interaction():
    data = request.get_json()
    log = InteractionLog(
        action=data.get('action'),
        description=data.get('description'),
        source='backend'
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Log recorded successfully'}), 201

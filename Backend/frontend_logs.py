from flask import Blueprint, request, jsonify, session
from models import db, ActionLog
from socketio_instance import socketio
import logging
import json
from datetime import datetime

frontend_logs_bp = Blueprint('frontend_logs', __name__, url_prefix='/api/logs')


@frontend_logs_bp.route('/', methods=['POST'])
def ingest_log():
    try:
        data = request.get_json(force=True) or {}
        action = data.get('action', 'frontend_event')
        description = json.dumps({
            "details": data.get('details'),
            "url": data.get('url', request.path),
            "userAgent": data.get('userAgent'),
            "meta": {
                "session_username": session.get('username'),
                "session_customer_id": session.get('customer_id'),
                "session_restaurant_id": session.get('restaurant_id')
            },
            "client_timestamp": data.get('timestamp', datetime.utcnow().isoformat())
        })
        log = ActionLog(action=action, description=description)
        db.session.add(log)
        db.session.commit()
        # Emit real-time event so frontend viewers can update
        try:
            socketio.emit('new_log', {
                'id': log.id,
                'action': log.action,
                'description': log.description,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            }, broadcast=True)
        except Exception:
            logging.exception('Failed to emit socket event for new log')
        return jsonify({'message': 'Logged'}), 201
    except Exception as e:
        logging.exception('Failed to ingest frontend log')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@frontend_logs_bp.route('/', methods=['GET'])
def get_logs():
    try:
        logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).all()
        result = [
            {
                'id': l.id,
                'action': l.action,
                'description': l.description,
                'timestamp': l.timestamp.isoformat() if l.timestamp else None
            }
            for l in logs
        ]
        return jsonify(result), 200
    except Exception as e:
        logging.exception('Failed to fetch frontend logs')
        return jsonify({'error': str(e)}), 500

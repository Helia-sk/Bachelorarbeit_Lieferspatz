from flask import Blueprint, request, jsonify
import os

# Define blueprint for logging endpoints
logging_bp = Blueprint('logging_bp', __name__)

# Path to the log file (assumed to be in the project root)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'user_actions.log')

from socketio_instance import socketio

@logging_bp.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open(LOG_FILE, 'r') as f:
            data = f.read()
        return jsonify({"logs": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@logging_bp.route('/logs_alt', methods=['GET'])
def get_logs_alt():
    try:
        with open(LOG_FILE, 'r') as f:
            data = f.read()
        return jsonify({"logs": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@logging_bp.route('/log', methods=['POST'])
def add_log():
    content = request.json.get("log", "")
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(content + "\n")
        socketio.emit("new_log", {"log": content})
        return jsonify({"status": "logged"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@logging_bp.route('/logs/reset', methods=['DELETE'])
def reset_logs():
    try:
        open(LOG_FILE, 'w').close()  # clear file
        socketio.emit("log_reset", {"status": "reset"})
        return jsonify({"status": "logs reset"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

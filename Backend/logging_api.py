from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import threading
import time
from typing import List, Dict, Any
import sqlite3

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
LOG_FILE = "user_interactions.json"
DB_FILE = "user_logs.db"
MAX_LOGS_IN_MEMORY = 1000

# In-memory storage for real-time access
logs_buffer: List[Dict[str, Any]] = []
connected_clients = set()

def init_database():
    """Initialize SQLite database for logs"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interactions (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            user_id TEXT,
            session_id TEXT,
            action TEXT,
            component TEXT,
            details TEXT,
            url TEXT,
            user_agent TEXT,
            viewport_width INTEGER,
            viewport_height INTEGER,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_sessions (
            session_id TEXT PRIMARY KEY,
            start_time TEXT,
            end_time TEXT,
            user_id TEXT,
            total_interactions INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def save_log_to_db(log_data: Dict[str, Any]):
    """Save log to SQLite database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_interactions 
            (id, timestamp, user_id, session_id, action, component, details, 
             url, user_agent, viewport_width, viewport_height, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data['id'],
            log_data['timestamp'],
            log_data.get('userId'),
            log_data['sessionId'],
            log_data['action'],
            log_data['component'],
            json.dumps(log_data['details']),
            log_data['url'],
            log_data['userAgent'],
            log_data['viewport']['width'],
            log_data['viewport']['height'],
            datetime.now().isoformat()
        ))
        
        # Update session info
        cursor.execute('''
            INSERT OR REPLACE INTO log_sessions 
            (session_id, start_time, user_id, total_interactions)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(session_id) DO UPDATE SET
            total_interactions = total_interactions + 1
        ''', (
            log_data['sessionId'],
            log_data['timestamp'],
            log_data.get('userId')
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving log to database: {e}")

def save_log_to_file(log_data: Dict[str, Any]):
    """Save log to JSON file (backup)"""
    try:
        # Ensure the file exists
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                json.dump([], f)
        
        # Read existing logs
        with open(LOG_FILE, 'r') as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
        
        # Add new log
        existing_logs.append(log_data)
        
        # Keep only recent logs in file (prevent file from growing too large)
        if len(existing_logs) > MAX_LOGS_IN_MEMORY:
            existing_logs = existing_logs[-MAX_LOGS_IN_MEMORY:]
        
        # Write back to file
        with open(LOG_FILE, 'w') as f:
            json.dump(existing_logs, f, indent=2)
            
    except Exception as e:
        print(f"Error saving log to file: {e}")

def broadcast_log(log_data: Dict[str, Any]):
    """Broadcast log to all connected clients"""
    socketio.emit('new_log', log_data, to=None)

@app.route('/api/logs', methods=['POST'])
def receive_logs():
    """Receive logs from frontend"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        
        if not isinstance(logs, list):
            return jsonify({'error': 'Invalid logs format'}), 400
        
        for log_data in logs:
            # Validate required fields
            required_fields = ['id', 'timestamp', 'sessionId', 'action', 'component']
            if not all(field in log_data for field in required_fields):
                continue
            
            # Add received timestamp
            log_data['received_at'] = datetime.now().isoformat()
            
            # Save to database
            save_log_to_db(log_data)
            
            # Save to file (backup)
            save_log_to_file(log_data)
            
            # Add to in-memory buffer
            logs_buffer.append(log_data)
            
            # Keep buffer size manageable
            if len(logs_buffer) > MAX_LOGS_IN_MEMORY:
                logs_buffer.pop(0)
            
            # Broadcast to connected clients
            broadcast_log(log_data)
        
        return jsonify({'message': f'Received {len(logs)} logs', 'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get logs with filtering options"""
    try:
        # Query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        action = request.args.get('action')
        component = request.args.get('component')
        session_id = request.args.get('session_id')
        user_id = request.args.get('user_id')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM user_interactions WHERE 1=1"
        params = []
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        logs = []
        for row in rows:
            log = {
                'id': row[0],
                'timestamp': row[1],
                'userId': row[2],
                'sessionId': row[3],
                'action': row[4],
                'component': row[5],
                'details': json.loads(row[6]) if row[6] else {},
                'url': row[7],
                'userAgent': row[8],
                'viewport': {
                    'width': row[9],
                    'height': row[10]
                },
                'createdAt': row[11]
            }
            logs.append(log)
        
        conn.close()
        
        return jsonify({
            'logs': logs,
            'total': len(logs),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/stats', methods=['GET'])
def get_log_stats():
    """Get log statistics"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Total logs
        cursor.execute("SELECT COUNT(*) FROM user_interactions")
        total_logs = cursor.fetchone()[0]
        
        # Actions breakdown
        cursor.execute("SELECT action, COUNT(*) FROM user_interactions GROUP BY action ORDER BY COUNT(*) DESC")
        actions_breakdown = dict(cursor.fetchall())
        
        # Components breakdown
        cursor.execute("SELECT component, COUNT(*) FROM user_interactions GROUP BY component ORDER BY COUNT(*) DESC")
        components_breakdown = dict(cursor.fetchall())
        
        # Sessions count
        cursor.execute("SELECT COUNT(*) FROM log_sessions")
        total_sessions = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM user_interactions 
            WHERE timestamp >= datetime('now', '-1 day')
        """)
        recent_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_logs': total_logs,
            'total_sessions': total_sessions,
            'recent_activity_24h': recent_activity,
            'actions_breakdown': actions_breakdown,
            'components_breakdown': components_breakdown
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/reset', methods=['POST'])
def reset_logs():
    """Reset all logs"""
    try:
        # Clear database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_interactions")
        cursor.execute("DELETE FROM log_sessions")
        conn.commit()
        conn.close()
        
        # Clear file
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                json.dump([], f)
        
        # Clear buffer
        logs_buffer.clear()
        
        # Broadcast reset event
        socketio.emit('logs_reset', {'message': 'All logs have been reset'}, to=None)
        
        return jsonify({'message': 'All logs have been reset', 'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/export', methods=['GET'])
def export_logs():
    """Export logs as JSON file"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_interactions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log = {
                'id': row[0],
                'timestamp': row[1],
                'userId': row[2],
                'sessionId': row[3],
                'action': row[4],
                'component': row[5],
                'details': json.loads(row[6]) if row[6] else {},
                'url': row[7],
                'userAgent': row[8],
                'viewport': {
                    'width': row[9],
                    'height': row[10]
                },
                'createdAt': row[11]
            }
            logs.append(log)
        
        conn.close()
        
        # Create export filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"user_logs_export_{timestamp}.json"
        
        # Save export file
        with open(export_filename, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return jsonify({
            'message': 'Logs exported successfully',
            'filename': export_filename,
            'total_logs': len(logs)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}")
    
    # Send current buffer to new client
    emit('logs_buffer', {'logs': logs_buffer[-100:]})  # Last 100 logs

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    print(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    init_database()
    print("Logging API initialized")
    print(f"Database: {DB_FILE}")
    print(f"Log file: {LOG_FILE}")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

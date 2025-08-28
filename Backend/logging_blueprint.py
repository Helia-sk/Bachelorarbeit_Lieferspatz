from flask import Blueprint, request, jsonify, render_template_string
from flask_socketio import emit
import json
import os
from datetime import datetime
import threading
import time
from typing import List, Dict, Any
import sqlite3
import logging
from csv_logger import csv_logger

# Create the logging blueprint
logging_bp = Blueprint('logging', __name__, url_prefix='/api/logs')

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_logs.db')
JSON_LOG_PATH = os.path.join(os.path.dirname(__file__), 'user_interactions.json')

def init_logging_database():
    """Initialize the logging database and tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop existing table if it exists to ensure correct schema
    cursor.execute('DROP TABLE IF EXISTS user_interactions')
    
    cursor.execute('''
        CREATE TABLE user_interactions (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            log_type TEXT NOT NULL,  -- 'frontend' or 'backend'
            schema_version TEXT,     -- e.g., 'login.v3', 'auth_result.v2'
            event_name TEXT NOT NULL, -- e.g., 'login_submit', 'login_attempt_result'
            session_id TEXT,
            attempt_id TEXT,
            browser_id TEXT,
            route TEXT,
            details TEXT NOT NULL,   -- JSON string with event-specific data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON user_interactions(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_type ON user_interactions(log_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_name ON user_interactions(event_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON user_interactions(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_schema_version ON user_interactions(schema_version)')
    
    conn.commit()
    conn.close()
    logging.info(f"Enhanced logging database initialized at {DB_PATH}")

def save_log_to_db(log_data: Dict[str, Any]):
    """Save a frontend log entry to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_interactions 
            (id, timestamp, log_type, schema_version, event_name, session_id, attempt_id, browser_id, route, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data['id'],
            log_data['timestamp'],
            'frontend',
            log_data.get('schema_version', 'frontend.v1'),
            log_data['event_name'],
            log_data.get('session_id'),
            log_data.get('attempt_id'),
            log_data.get('browser_id'),
            log_data.get('route'),
            json.dumps(log_data)
        ))
        conn.commit()
        logging.info(f"Frontend log saved: {log_data['event_name']}")
    except Exception as e:
        logging.error(f"Error saving frontend log to database: {e}")
        logging.error(f"Log data: {log_data}")
        conn.rollback()
    finally:
        conn.close()

def save_backend_log_to_db(log_data: Dict[str, Any]):
    """Save a backend log entry to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_interactions 
            (id, timestamp, log_type, schema_version, event_name, session_id, attempt_id, browser_id, route, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_data['id'],
            log_data['timestamp'],
            'backend',
            log_data.get('schema_version', 'backend.v1'),
            log_data['event_name'],
            log_data.get('session_id'),
            log_data.get('attempt_id'),
            log_data.get('browser_id'),
            log_data.get('route'),
            json.dumps(log_data)
        ))
        conn.commit()
        logging.info(f"Backend log saved: {log_data['event_name']}")
    except Exception as e:
        logging.error(f"Error saving backend log to database: {e}")
        logging.error(f"Log data: {log_data}")
        conn.rollback()
    finally:
        conn.close()

def save_log_to_file(log_data: Dict[str, Any]):
    """Save log to JSON file as backup"""
    try:
        logs = []
        if os.path.exists(JSON_LOG_PATH):
            with open(JSON_LOG_PATH, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        
        logs.append(log_data)
        
        # Keep only last 1000 logs to prevent file from growing too large
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        with open(JSON_LOG_PATH, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving log to file: {e}")

def broadcast_log(log_data: Dict[str, Any]):
    """Broadcast log to all connected clients via WebSocket"""
    # This will be called from the main app's socketio instance
    pass

# Initialize database when blueprint is created
init_logging_database()

@logging_bp.route('/', methods=['POST', 'OPTIONS'])
def receive_logs():
    """Receive logs from frontend"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        data = request.get_json()
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs data provided'}), 400
        
        logs = data['logs']
        if not isinstance(logs, list):
            return jsonify({'error': 'Logs must be an array'}), 400
        
        logging.info(f"Received {len(logs)} logs from frontend")
        
        for log in logs:
            # Validate required fields for new format
            required_fields = ['id', 'timestamp', 'event_name']
            for field in required_fields:
                if field not in log:
                    logging.warning(f"Missing required field: {field}")
                    continue
            
            # Save to database
            save_log_to_db(log)
            
            # Save to file as backup
            save_log_to_file(log)
            
            # Broadcast to connected clients (will be handled by main app)
            broadcast_log(log)
        
        response = jsonify({'message': f'Successfully received {len(logs)} logs', 'status': 'success'})
        return response
    
    except Exception as e:
        logging.error(f"Error processing logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/', methods=['GET', 'OPTIONS'])
def get_logs():
    """Get logs with optional filtering and pagination"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        action = request.args.get('action')
        component = request.args.get('component')
        session_id = request.args.get('session_id')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM user_interactions WHERE 1=1"
        params = []
        
        if action:
            query += " AND event_name = ?"
            params.append(action)
        
        if component:
            query += " AND schema_version = ?"
            params.append(component)
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to log objects with new schema
        logs = []
        for row in rows:
            log = {
                'id': row[0],
                'timestamp': row[1],
                'log_type': row[2],
                'schema_version': row[3],
                'event_name': row[4],
                'session_id': row[5],
                'attempt_id': row[6],
                'browser_id': row[7],
                'route': row[8],
                'details': json.loads(row[9]) if row[9] else {}
            }
            logs.append(log)
        
        conn.close()
        
        response = jsonify({'logs': logs, 'total': len(logs), 'limit': limit, 'offset': offset})
        return response
    
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/stats', methods=['GET', 'OPTIONS'])
def get_log_stats():
    """Get logging statistics"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total logs
        cursor.execute("SELECT COUNT(*) FROM user_interactions")
        total_logs = cursor.fetchone()[0]
        
        # Total sessions
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM user_interactions")
        total_sessions = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM user_interactions 
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent_activity_24h = cursor.fetchone()[0]
        
        # Events breakdown
        cursor.execute("""
            SELECT event_name, COUNT(*) as count 
            FROM user_interactions 
            GROUP BY event_name 
            ORDER BY count DESC
        """)
        events_breakdown = dict(cursor.fetchall())
        
        # Schema breakdown
        cursor.execute("""
            SELECT schema_version, COUNT(*) as count 
            FROM user_interactions 
            GROUP BY schema_version 
            ORDER BY count DESC
        """)
        schemas_breakdown = dict(cursor.fetchall())
        
        conn.close()
        
        stats = {
            'total_logs': total_logs,
            'total_sessions': total_sessions,
            'recent_activity_24h': recent_activity_24h,
            'events_breakdown': events_breakdown,
            'schemas_breakdown': schemas_breakdown
        }
        
        response = jsonify(stats)
        return response
    
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/reset', methods=['POST', 'OPTIONS'])
def reset_logs():
    """Reset all logs"""
    logging.info(f"Reset request received: method={request.method}, content_type={request.content_type}")
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        logging.info(f"Database path: {DB_PATH}")
        logging.info(f"Database exists: {os.path.exists(DB_PATH)}")
        
        logging.info("Connecting to database...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_interactions'")
        table_exists = cursor.fetchone()
        logging.info(f"Table exists: {table_exists}")
        
        if table_exists:
            logging.info("Clearing database...")
            # Clear database
            cursor.execute("DELETE FROM user_interactions")
            deleted_count = cursor.rowcount
            conn.commit()
            logging.info(f"Database cleared successfully. Deleted {deleted_count} rows")
        else:
            logging.warning("Table doesn't exist, creating it...")
            init_logging_database()
            logging.info("Table created successfully")
        
        conn.close()
        
        # Clear JSON file if it exists
        try:
            if os.path.exists(JSON_LOG_PATH):
                os.remove(JSON_LOG_PATH)
                logging.info("JSON log file removed")
        except Exception as file_error:
            logging.warning(f"Could not remove JSON file: {file_error}")
        
        logging.info("All logs have been reset successfully")
        
        response = jsonify({'message': 'All logs have been reset successfully'})
        return response
    
    except Exception as e:
        logging.error(f"Error resetting logs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/export', methods=['GET', 'OPTIONS'])
def export_logs():
    """Export logs as JSON file"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_interactions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        # Convert rows to log objects
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
                }
            }
            logs.append(log)
        
        conn.close()
        
        # Create export filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_interactions_export_{timestamp}.json'
        export_path = os.path.join(os.path.dirname(__file__), filename)
        
        # Write export file
        with open(export_path, 'w') as f:
            json.dump(logs, f, indent=2)
        
        response = jsonify({
            'message': f'Exported {len(logs)} logs successfully',
            'filename': filename,
            'total_logs': len(logs)
        })
        return response
    
    except Exception as e:
        logging.error(f"Error exporting logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/backend', methods=['POST', 'OPTIONS'])
def receive_backend_logs():
    """Receive backend logs from server-side code"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        data = request.get_json()
        if not data or 'logs' not in data:
            return jsonify({'error': 'No logs data provided'}), 400
        
        logs = data['logs']
        if not isinstance(logs, list):
            return jsonify({'error': 'Logs must be an array'}), 400
        
        logging.info(f"Received {len(logs)} backend logs")
        
        for log in logs:
            # Validate required fields for new format
            required_fields = ['id', 'timestamp', 'event_name']
            for field in required_fields:
                if field not in log:
                    logging.warning(f"Missing required field: {field}")
                    continue
            
            # Save to database
            save_log_to_db(log)
            
            # Broadcast to connected clients
            broadcast_log(log)
        
        response = jsonify({'message': f'Successfully received {len(logs)} backend logs', 'status': 'success'})
        return response
    
    except Exception as e:
        logging.error(f"Error processing backend logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_interactions")
        total_logs = cursor.fetchone()[0]
        conn.close()
        
        response = jsonify({
            'status': 'healthy',
            'database': 'connected',
            'total_logs': total_logs,
            'timestamp': datetime.now().isoformat()
        })
        return response
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@logging_bp.route('/csv', methods=['POST', 'OPTIONS'])
def receive_csv_logs():
    """Receive CSV format logs from frontend"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        data = request.get_json()
        if not data or 'csv_data' not in data:
            return jsonify({'error': 'No CSV data provided'}), 400
        
        csv_lines = data['csv_data']
        if not isinstance(csv_lines, list):
            return jsonify({'error': 'CSV data must be an array'}), 400
        
        logging.info(f"Received {len(csv_lines)} CSV log lines")
        
        # Log to CSV file
        csv_logger.log_frontend_batch(csv_lines)
        
        response = jsonify({'message': f'Successfully received {len(csv_lines)} CSV log lines', 'status': 'success'})
        return response
        
    except Exception as e:
        logging.error(f"Error processing CSV logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/csv/stats', methods=['GET', 'OPTIONS'])
def get_csv_stats():
    """Get CSV log file statistics"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        stats = csv_logger.get_csv_stats()
        response = jsonify({
            'status': 'success',
            'csv_stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        return response
        
    except Exception as e:
        logging.error(f"Error getting CSV stats: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/csv/download', methods=['GET', 'OPTIONS'])
def download_csv_logs():
    """Download CSV log files"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        from flask import send_file
        import tempfile
        import zipfile
        
        # Create a temporary zip file containing both CSV files
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                # Add frontend CSV if it exists
                if os.path.exists(csv_logger.frontend_csv_file):
                    zip_file.write(csv_logger.frontend_csv_file, 'frontend_logs.csv')
                
                # Add backend CSV if it exists
                if os.path.exists(csv_logger.backend_csv_file):
                    zip_file.write(csv_logger.backend_csv_file, 'backend_logs.csv')
            
            temp_zip_path = temp_zip.name
        
        # Send the zip file
        return send_file(
            temp_zip_path,
            as_attachment=True,
            download_name=f'logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logging.error(f"Error downloading CSV logs: {e}")
        return jsonify({'error': str(e)}), 500

@logging_bp.route('/csv/clear', methods=['POST', 'OPTIONS'])
def clear_csv_logs():
    """Clear CSV log files"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    try:
        csv_logger.clear_csv_files()
        
        response = jsonify({
            'message': 'CSV log files cleared successfully',
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })
        return response
        
    except Exception as e:
        logging.error(f"Error clearing CSV logs: {e}")
        return jsonify({'error': str(e)}), 500

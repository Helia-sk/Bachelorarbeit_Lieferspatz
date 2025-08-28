from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import logging
import sys
import os
from models import db
from session_config import init_session
from socketio_instance import socketio
from logout import logout_bp
#Customer blueprints
from customer_restaurant_details import restaurant_details_bp
from customer_place_order import customer_place_order_bp
from customer_login import customer_login_bp
from customer_reg import customer_register_bp
from nearby_restaurants import nearby_restaurants_bp
from cus_balance import cus_balance_bp
from cus_orders import cus_orders_bp
#restaurabnt blueprints
from restaurant_reg import register_bp
from restaurant_login import login_bp
from Res_opening_hours import settings_bp
from Res_delivery_area import delivery_bp
from Res_Profile import profile_bp
from Res_balance import balance_bp
from Res_orders import orders_bp
from menu import menu_bp
#Logging blueprint
from logging_blueprint import logging_bp


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__)

    # 1. Configure the app
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'Hi'

    # 2. Initialize the database
    db.init_app(app)

    # 3. Initialize session management with the db
    init_session(app, db)

    # 4. Configure CORS to allow credentials and specify the correct origin
    CORS(app, 
          supports_credentials=True, 
          origins=["*"],  # Allow all origins for development
          methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
          allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
    )

    # 5. Initialize WebSockets
    socketio.init_app(app)

    # 6. Initialize Bcrypt
    bcrypt = Bcrypt(app)
    Migrate(app, db)

    # 7. Register Blueprints
    app.register_blueprint(register_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(delivery_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(balance_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(customer_login_bp)
    app.register_blueprint(customer_register_bp)
    app.register_blueprint(nearby_restaurants_bp)
    app.register_blueprint(restaurant_details_bp)  
    app.register_blueprint(customer_place_order_bp)
    app.register_blueprint(cus_balance_bp)
    app.register_blueprint(cus_orders_bp)
    app.register_blueprint(logging_bp) 

    # 8. Add WebSocket event handlers
    @socketio.on('connect')
    def handle_connect():
        logging.info("A client connected via WebSocket")

    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info("A client disconnected from WebSocket")
    
    # Logging WebSocket events
    @socketio.on('new_log')
    def handle_new_log(data):
        logging.info(f"New log received via WebSocket: {data}")
        socketio.emit('new_log', data, to=None)
    
    @socketio.on('logs_reset')
    def handle_logs_reset():
        logging.info("Logs reset requested via WebSocket")
        socketio.emit('logs_reset', {'message': 'All logs have been reset'}, to=None)

    # Helper function to determine if an endpoint is a business API
    def is_business_endpoint(path: str) -> bool:
        """Check if a given URL path corresponds to a business API endpoint."""
        business_endpoints = [
            '/api/customer/',
            '/api/restaurant/',
            '/api/orders/',
            '/api/menu/',
            '/api/auth/',
            '/api/balance/',
            '/api/delivery/',
            '/api/profile/',
            '/api/settings/',
            '/api/nearby/',
            '/api/restaurant-details/',
            '/api/place-order/',
            '/api/balance/',
            '/api/orders/',
            '/api/menu/',
            '/api/logout',
            '/api/register',
            '/api/login'
        ]
        
        # Explicitly exclude logging system endpoints
        if path.startswith('/api/logs') or path.startswith('/health') or path.startswith('/metrics'):
            return False
            
        # Check if path matches any business endpoint
        return any(path.startswith(endpoint) for endpoint in business_endpoints)

    # 9. Utility route to list all available routes
    @app.route('/routes', methods=['GET'])
    def list_routes():
        routes = {rule.rule: list(rule.methods) for rule in app.url_map.iter_rules()}
        return jsonify(routes)

    # 10. Log all incoming requests for debugging
    @app.before_request
    def log_request_info():
        # Skip logging for logging system endpoints to prevent infinite loops
        if request.path.startswith('/api/logs'):
            return
        logging.info(f"Received {request.method} request to {request.url}")
        logging.info(f"Headers: {dict(request.headers)}")
        
        # Skip logging body for export requests to avoid logging large amounts of data
        if request.method in ["POST", "PUT", "PATCH"] and "/export" not in request.url:
            try:
                body = request.get_json() if request.content_type == 'application/json' else request.get_data()
                logging.info(f"Body: {body}")
            except Exception as e:
                logging.info(f"Body: Could not parse - {e}")
                logging.info(f"Raw data: {request.get_data()}")
        elif "/export" in request.url:
            logging.info("Body: Skipped logging for export request (large data)")
        
        # Only log backend activity for business API endpoints
        if is_business_endpoint(request.path):
            try:
                from logging_blueprint import save_backend_log_to_db
                from csv_logger import csv_logger
                import uuid
                from datetime import datetime
                
                backend_log = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'event': 'http_request',
                    'schema': 'http_request.v1',
                    'session_id': 'backend',
                    'attempt_id': str(uuid.uuid4()),
                    'browser_id': 'backend',
                    'route': request.path,
                    'details': {
                        'method': request.method,
                        'url': request.url,
                        'endpoint': request.endpoint,
                        'status_code': None,  # Will be set in after_request
                        'user_agent': request.headers.get('User-Agent', 'Unknown'),
                        'ip_address': request.remote_addr,
                        'content_type': request.content_type,
                        'content_length': request.content_length
                    }
                }
                
                # Dual logging: Save to database AND CSV
                save_backend_log_to_db(backend_log)
                csv_logger.log_backend(backend_log)
                
            except Exception as e:
                logging.error(f"Failed to log backend activity: {e}")
    
    # 11. Log response status codes
    @app.after_request
    def log_response_info(response):
        # Skip logging for logging system endpoints to prevent infinite loops
        if request.path.startswith('/api/logs'):
            return response
            
        # Only log backend activity for business API endpoints
        if is_business_endpoint(request.path):
            try:
                from logging_blueprint import save_backend_log_to_db
                from csv_logger import csv_logger
                import uuid
                from datetime import datetime
                
                # Log response status
                backend_log = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'event': 'http_response',
                    'schema': 'http_response.v1',
                    'session_id': 'backend',
                    'attempt_id': str(uuid.uuid4()),
                    'browser_id': 'backend',
                    'route': request.path,
                    'details': {
                        'method': request.method,
                        'url': request.url,
                        'endpoint': request.endpoint,
                        'status_code': response.status_code,
                        'response_size': len(response.get_data()),
                        'content_type': response.content_type,
                        'processing_time': None  # Could be enhanced with timing
                    }
                }
                
                # Dual logging: Save to database AND CSV
                save_backend_log_to_db(backend_log)
                csv_logger.log_backend(backend_log)
                
            except Exception as e:
                logging.error(f"Failed to log response info: {e}")
        
        return response

    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, debug=True, host='localhost', port=5050)
from flask import Blueprint, request, jsonify, session
from flask_bcrypt import Bcrypt
from models import db, Customer
from utils import validate_request
import logging
# Backend logging disabled to prevent infinite loops
# from backend_logger import log_backend_action, log_backend_event

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bcrypt = Bcrypt()

# Blueprint for customer login
customer_login_bp = Blueprint('customer_login', __name__)

@customer_login_bp.route('/api/customer/login', methods=['POST'])
def login():
    try:
        # Retrieve JSON data from the request
        data = request.get_json()
        logging.info(f"Received customer login data: {data}")

        # Log login attempt (disabled to prevent infinite loops)
        # log_backend_action(
        #     action='login_attempt',
        #     component='customer_auth',
        #     details={
        #         'username': data.get('username'),
        #         'ip_address': request.remote_addr,
        #         'user_agent': request.headers.get('User-Agent', 'Unknown')
        #     },
        #     route=request.path
        # )

        # Validate input fields
        validation_error = validate_request(data, ['username', 'password'])
        if validation_error:
            logging.warning(f"Validation failed: {validation_error}")
            
            # Log validation failure (disabled to prevent infinite loops)
            # log_backend_action(
            #     action='login_validation_failed',
            #     component='customer_auth',
            #     details={
            #         'username': data.get('username'),
            #         'validation_error': str(validation_error),
            #         'ip_address': request.remote_addr
            #     },
            #     route=request.path
            # )
            
            return jsonify(validation_error), 400

        # Query the customer by username
        customer = Customer.query.filter_by(username=data['username']).first()

        # Verify the password
        if customer and bcrypt.check_password_hash(customer.password_hash, data['password']):
            # Set session details
            session['username'] = customer.username
            session['customer_id'] = customer.id
            logging.info(f"Login successful for customer: {customer.username}, Session Data: {dict(session)}")

            # Log successful login (disabled to prevent infinite loops)
            # log_backend_action(
            #     action='login_success',
            #     component='customer_auth',
            #     details={
            #         'username': customer.username,
            #         'customer_id': customer.id,
            #         'ip_address': request.remote_addr,
            #         'session_id': session.get('session_id', 'unknown')
            #     },
            #         user_id=str(customer.id),
            #         route=request.path
            #     )

            # Log the session cookie value for debugging
            session_cookie = request.cookies.get('app_session')
            logging.info(f"Session cookie set: {session_cookie}")

            return jsonify({
                'message': 'Login successful',
                'customer_id': customer.id,
                'postal_code': customer.postal_code  
            }), 200

        logging.warning("Invalid username or password")
        
        # Log failed login attempt (disabled to prevent infinite loops)
        # log_backend_action(
        #     action='login_failed',
        #     component='customer_auth',
        #     details={
        #         'username': data.get('username'),
        #         'reason': 'Invalid username or password',
        #         'ip_address': request.remote_addr
        #     },
        #     route=request.path
        # )
        
        return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        logging.error(f"Error during customer login: {e}")
        
        # Log error (disabled to prevent infinite loops)
        # log_backend_event(
        #     event='login_error',
        #     details={
        #         'username': data.get('username') if 'data' in locals() else 'unknown',
        #         'error_message': str(e),
        #         'ip_address': request.remote_addr,
        #         'route': request.path
        #     },
        #     route=request.path
        # )
        
        return jsonify({'error': 'Internal server error'}), 500

@customer_login_bp.route('/session', methods=['GET'])
def check_session():
    if 'username' in session:
        # Log session check success (disabled to prevent infinite loops)
        # log_backend_action(
        #     action='session_check_success',
        #     component='customer_auth',
        #     details={
        #         'username': session['username'],
        #         'customer_id': session['customer_id'],
        #         'ip_address': request.remote_addr
        #     },
        #     user_id=str(session['customer_id']),
        #     route=request.path
        #     )
        return jsonify({'username': session['username'], 'customer_id': session['customer_id']}), 200
    
    # Log session check failure (disabled to prevent infinite loops)
    # log_backend_action(
    #     action='session_check_failed',
    #     component='customer_auth',
    #     details={
    #         'ip_address': request.remote_addr,
    #         'reason': 'No active session'
    #     },
    #     route=request.path
    # )
    return jsonify({'error': 'No active session'}), 401

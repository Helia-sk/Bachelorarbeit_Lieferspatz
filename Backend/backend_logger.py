#!/usr/bin/env python3
"""
Backend Logging Utility
Simple functions to log backend actions and events
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import requests
import json
import logging

# Configuration
LOGGING_API_URL = "http://localhost:5050/api/logs/backend"
# DISABLED: This creates infinite loops when backend tries to log to logging API
# The backend logging is now handled directly in FLASK_APP.py via before_request/after_request hooks
ENABLE_LOGGING = False

def log_backend_action(
    action: str,
    component: str,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    route: Optional[str] = None,
    user_id: Optional[str] = None,
    schema_version: str = "backend.v1"
) -> bool:
    """
    Log a backend action to the logging system
    
    Args:
        action: The action being performed (e.g., 'user_login', 'order_created')
        component: The component/module performing the action (e.g., 'auth', 'orders')
        details: Additional details about the action
        session_id: Session identifier if available
        route: API route or endpoint being called
        user_id: User identifier if available
        schema_version: Schema version for the log entry
    
    Returns:
        bool: True if logging was successful, False otherwise
    """
    if not ENABLE_LOGGING:
        return False
    
    try:
        # Create log entry
        log_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'component': component,
            'log_type': 'backend',
            'schema': schema_version,
            'session_id': session_id or 'backend',
            'attempt_id': str(uuid.uuid4()),
            'browser_id': user_id or 'backend',
            'route': route or 'unknown',
            'details': details or {}
        }
        
        # Send to logging API
        response = requests.post(
            LOGGING_API_URL,
            json={'logs': [log_entry]},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            logging.debug(f"Backend action logged successfully: {action}")
            return True
        else:
            logging.warning(f"Failed to log backend action: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error logging backend action: {e}")
        return False

def log_backend_event(
    event: str,
    details: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    route: Optional[str] = None,
    user_id: Optional[str] = None,
    schema_version: str = "backend.v1"
) -> bool:
    """
    Log a backend event to the logging system
    
    Args:
        event: The event that occurred (e.g., 'database_error', 'api_timeout')
        details: Additional details about the event
        session_id: Session identifier if available
        route: API route or endpoint where event occurred
        user_id: User identifier if available
        schema_version: Schema version for the log entry
    
    Returns:
        bool: True if logging was successful, False otherwise
    """
    if not ENABLE_LOGGING:
        return False
    
    try:
        # Create log entry
        log_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'log_type': 'backend',
            'schema': schema_version,
            'session_id': session_id or 'backend',
            'attempt_id': str(uuid.uuid4()),
            'browser_id': user_id or 'backend',
            'route': route or 'unknown',
            'details': details or {}
        }
        
        # Send to logging API
        response = requests.post(
            LOGGING_API_URL,
            json={'logs': [log_entry]},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            logging.debug(f"Backend event logged successfully: {event}")
            return True
        else:
            logging.warning(f"Failed to log backend event: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error logging backend event: {e}")
        return False

# Convenience functions for common backend actions
def log_user_login(user_id: str, success: bool, details: Optional[Dict[str, Any]] = None) -> bool:
    """Log user login attempt"""
    action = 'login_success' if success else 'login_failed'
    return log_backend_action(
        action=action,
        component='auth',
        details={
            'user_id': user_id,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            **(details or {})
        },
        user_id=user_id
    )

def log_order_created(order_id: str, user_id: str, order_details: Dict[str, Any]) -> bool:
    """Log order creation"""
    return log_backend_action(
        action='order_created',
        component='orders',
        details={
            'order_id': order_id,
            'user_id': user_id,
            'order_details': order_details,
            'timestamp': datetime.now().isoformat()
        },
        user_id=user_id
    )

def log_database_query(query_type: str, table: str, success: bool, duration_ms: float = None) -> bool:
    """Log database query"""
    return log_backend_action(
        action='database_query',
        component='database',
        details={
            'query_type': query_type,
            'table': table,
            'success': success,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
    )

def log_api_request(method: str, endpoint: str, status_code: int, duration_ms: float = None) -> bool:
    """Log API request"""
    return log_backend_action(
        action='api_request',
        component='api',
        details={
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
    )

def log_error(error_type: str, error_message: str, stack_trace: str = None, context: Dict[str, Any] = None) -> bool:
    """Log backend error"""
    return log_backend_event(
        event='error',
        details={
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
    )

# Example usage:
if __name__ == "__main__":
    # Test the logging functions
    print("Testing backend logging...")
    
    # Log a user login
    log_user_login("user123", True, {"ip": "192.168.1.1"})
    
    # Log an order creation
    log_order_created("order456", "user123", {"items": 3, "total": 45.99})
    
    # Log a database query
    log_database_query("SELECT", "users", True, 15.5)
    
    # Log an API request
    log_api_request("POST", "/api/orders", 201, 125.0)
    
    # Log an error
    log_error("DatabaseError", "Connection timeout", "Traceback...", {"table": "users"})
    
    print("Backend logging test completed!")

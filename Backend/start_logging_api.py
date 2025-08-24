#!/usr/bin/env python3
"""
Startup script for the User Interaction Logging API
Run this script to start the logging server
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages if not already installed"""
    try:
        import flask
        import flask_cors
        import flask_socketio
        print("✓ All required packages are already installed")
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "logging_requirements.txt"])
        print("✓ Required packages installed successfully")

def start_server():
    """Start the logging API server"""
    print("Starting User Interaction Logging API...")
    print("Server will be available at: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Import and run the logging API
    from logging_api import app, socketio
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    try:
        install_requirements()
        start_server()
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

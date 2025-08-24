#!/usr/bin/env python3
"""
Script to install dependencies and start the integrated Flask app with logging functionality.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install the required packages"""
    print("📦 Installing Flask-SocketIO dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask-SocketIO==5.3.6", "python-socketio==5.8.0", "python-engineio==4.7.1"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def start_app():
    """Start the integrated Flask app"""
    print("🚀 Starting integrated Flask app with logging...")
    try:
        # Change to the Backend directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the app
        subprocess.run([sys.executable, "FLASK_APP.py"])
    except KeyboardInterrupt:
        print("\n🛑 App stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")

def main():
    print("🔧 Setting up integrated Flask app with logging...")
    
    # Install dependencies
    if not install_requirements():
        print("❌ Failed to install dependencies. Exiting.")
        return
    
    # Start the app
    start_app()

if __name__ == "__main__":
    main()

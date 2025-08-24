#!/usr/bin/env python3
"""
Start script for the Logging Dashboard
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Logging Dashboard...")
    print("📊 This will run on port 5001")
    print("🔗 Make sure your main Flask app is running on port 5050")
    print("")
    
    try:
        # Change to the Backend directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the dashboard
        print("✅ Starting dashboard...")
        subprocess.run([sys.executable, "logging_dashboard.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()

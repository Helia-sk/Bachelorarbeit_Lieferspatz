#!/usr/bin/env python3
"""
Test script to verify backend logging functionality
"""

import requests
import json
from datetime import datetime

def test_backend_logging():
    """Test the backend logging system"""
    
    # Test data
    test_logs = [
        {
            'id': f'test_{datetime.now().isoformat()}',
            'timestamp': datetime.now().isoformat(),
            'action': 'test_action',
            'component': 'test_component',
            'log_type': 'backend',
            'schema': 'test.v1',
            'session_id': 'test_session',
            'attempt_id': f'test_attempt_{datetime.now().isoformat()}',
            'browser_id': 'test_user',
            'route': '/test/endpoint',
            'details': {
                'test_field': 'test_value',
                'timestamp': datetime.now().isoformat()
            }
        },
        {
            'id': f'test_event_{datetime.now().isoformat()}',
            'timestamp': datetime.now().isoformat(),
            'event': 'test_event',
            'log_type': 'backend',
            'schema': 'test.v1',
            'session_id': 'test_session',
            'attempt_id': f'test_event_attempt_{datetime.now().isoformat()}',
            'browser_id': 'test_user',
            'route': '/test/event',
            'details': {
                'event_type': 'test',
                'severity': 'info',
                'timestamp': datetime.now().isoformat()
            }
        }
    ]
    
    print("🧪 Testing Backend Logging System...")
    print("=" * 50)
    
    # Test 1: Send logs to backend endpoint
    print("📤 Test 1: Sending logs to backend endpoint...")
    try:
        response = requests.post(
            'http://localhost:5050/api/logs/backend',
            json={'logs': test_logs},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Successfully sent logs to backend endpoint")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed to send logs: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure your Flask app is running on port 5050")
        return
    except Exception as e:
        print(f"❌ Error sending logs: {e}")
        return
    
    print()
    
    # Test 2: Retrieve logs to verify they were saved
    print("📥 Test 2: Retrieving logs to verify they were saved...")
    try:
        response = requests.get(
            'http://localhost:5050/api/logs?limit=10',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            # Find our test logs
            test_logs_found = []
            for log in logs:
                if log.get('id', '').startswith('test_'):
                    test_logs_found.append(log)
            
            if test_logs_found:
                print(f"✅ Found {len(test_logs_found)} test logs in the system")
                for log in test_logs_found:
                    print(f"   - {log.get('event_name', log.get('action', 'unknown'))} ({log.get('log_type', 'unknown')})")
            else:
                print("⚠️  No test logs found - they may not have been saved correctly")
                
        else:
            print(f"❌ Failed to retrieve logs: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error retrieving logs: {e}")
    
    print()
    
    # Test 3: Check logs by type
    print("🔍 Test 3: Checking logs by type...")
    try:
        response = requests.get(
            'http://localhost:5050/api/logs?log_type=backend&limit=5',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            backend_logs = data.get('logs', [])
            
            if backend_logs:
                print(f"✅ Found {len(backend_logs)} backend logs")
                for log in backend_logs[:3]:  # Show first 3
                    print(f"   - {log.get('event_name', log.get('action', 'unknown'))} at {log.get('timestamp', 'unknown')}")
            else:
                print("⚠️  No backend logs found")
                
        else:
            print(f"❌ Failed to retrieve backend logs: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking logs by type: {e}")
    
    print()
    
    # Test 4: Test the backend_logger utility
    print("🛠️  Test 4: Testing backend_logger utility...")
    try:
        from backend_logger import log_backend_action, log_backend_event
        
        # Test logging an action
        success = log_backend_action(
            action='test_utility_action',
            component='test_utility',
            details={'test': True, 'timestamp': datetime.now().isoformat()},
            route='/test/utility'
        )
        
        if success:
            print("✅ Successfully logged action using backend_logger utility")
        else:
            print("❌ Failed to log action using backend_logger utility")
        
        # Test logging an event
        success = log_backend_event(
            event='test_utility_event',
            details={'test': True, 'timestamp': datetime.now().isoformat()},
            route='/test/utility'
        )
        
        if success:
            print("✅ Successfully logged event using backend_logger utility")
        else:
            print("❌ Failed to log event using backend_logger utility")
            
    except ImportError as e:
        print(f"❌ Could not import backend_logger: {e}")
    except Exception as e:
        print(f"❌ Error testing backend_logger utility: {e}")
    
    print()
    print("=" * 50)
    print("🏁 Backend Logging Test Completed!")
    print()
    print("📋 Next Steps:")
    print("1. Check your logging dashboard to see if backend logs appear")
    print("2. Verify that logs show up in the database")
    print("3. Test with real backend actions (login, orders, etc.)")
    print("4. Monitor the console for any error messages")

if __name__ == "__main__":
    test_backend_logging()

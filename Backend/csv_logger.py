#!/usr/bin/env python3
"""
Backend CSV Logger
Handles CSV format logging alongside the existing logging system
"""

import csv
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

class CSVLogger:
    def __init__(self, log_dir: str = None):
        """Initialize CSV logger with specified directory"""
        if log_dir is None:
            log_dir = os.path.dirname(__file__)
        
        self.log_dir = log_dir
        self.frontend_csv_file = os.path.join(log_dir, 'frontend_logs.csv')
        self.backend_csv_file = os.path.join(log_dir, 'backend_logs.csv')
        
        # Ensure CSV files exist with headers
        self.ensure_headers()
        
        logging.info(f"CSV Logger initialized. Frontend: {self.frontend_csv_file}, Backend: {self.backend_csv_file}")
    
    def ensure_headers(self):
        """Create CSV files with headers if they don't exist"""
        # Frontend logs headers
        frontend_headers = [
            'timestamp', 'event', 'session_id', 'route', 'method', 'status_code',
            'user_id', 'ip_address', 'component', 'action', 'browser_id',
            'attempt_id', 'details'
        ]
        
        # Backend logs headers
        backend_headers = [
            'timestamp', 'event', 'route', 'method', 'status_code', 'ip_address',
            'user_agent', 'content_type', 'response_size', 'session_id'
        ]
        
        # Create frontend CSV if it doesn't exist
        if not os.path.exists(self.frontend_csv_file):
            with open(self.frontend_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(frontend_headers)
            logging.info(f"Created frontend CSV file: {self.frontend_csv_file}")
        
        # Create backend CSV if it doesn't exist
        if not os.path.exists(self.backend_csv_file):
            with open(self.backend_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(backend_headers)
            logging.info(f"Created backend CSV file: {self.backend_csv_file}")
    
    def log_frontend(self, log_data: Dict[str, Any]):
        """Log frontend interaction to CSV"""
        try:
            csv_line = [
                log_data.get('timestamp', ''),
                log_data.get('event', ''),
                log_data.get('session_id', ''),
                log_data.get('route', ''),
                log_data.get('method', ''),
                log_data.get('status_code', ''),
                log_data.get('user_id', ''),
                log_data.get('ip_address', ''),
                log_data.get('component', ''),
                log_data.get('action', ''),
                log_data.get('browser_id', ''),
                log_data.get('attempt_id', ''),
                json.dumps(log_data.get('details', {})) if log_data.get('details') else ''
            ]
            
            with open(self.frontend_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(csv_line)
                
        except Exception as e:
            logging.error(f"Failed to log frontend data to CSV: {e}")
    
    def log_backend(self, log_data: Dict[str, Any]):
        """Log backend request/response to CSV"""
        try:
            details = log_data.get('details', {})
            csv_line = [
                log_data.get('timestamp', ''),
                log_data.get('event', ''),
                log_data.get('route', ''),
                details.get('method', ''),
                details.get('status_code', ''),
                details.get('ip_address', ''),
                details.get('user_agent', ''),
                details.get('content_type', ''),
                details.get('response_size', ''),
                log_data.get('session_id', '')
            ]
            
            with open(self.backend_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(csv_line)
                
        except Exception as e:
            logging.error(f"Failed to log backend data to CSV: {e}")
    
    def log_frontend_batch(self, csv_lines: List[str]):
        """Log multiple frontend CSV lines at once"""
        try:
            with open(self.frontend_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for line in csv_lines:
                    # Parse the CSV line and write it
                    if line.strip():
                        writer.writerow(line.split(','))
                        
        except Exception as e:
            logging.error(f"Failed to log frontend batch to CSV: {e}")
    
    def get_csv_stats(self) -> Dict[str, Any]:
        """Get statistics about CSV log files"""
        stats = {}
        
        try:
            # Frontend CSV stats
            if os.path.exists(self.frontend_csv_file):
                with open(self.frontend_csv_file, 'r', encoding='utf-8') as csvfile:
                    frontend_lines = sum(1 for line in csvfile) - 1  # Subtract header
                stats['frontend_lines'] = frontend_lines
                stats['frontend_size_mb'] = round(os.path.getsize(self.frontend_csv_file) / (1024 * 1024), 2)
            
            # Backend CSV stats
            if os.path.exists(self.backend_csv_file):
                with open(self.backend_csv_file, 'r', encoding='utf-8') as csvfile:
                    backend_lines = sum(1 for line in csvfile) - 1  # Subtract header
                stats['backend_lines'] = backend_lines
                stats['backend_size_mb'] = round(os.path.getsize(self.backend_csv_file) / (1024 * 1024), 2)
                
        except Exception as e:
            logging.error(f"Failed to get CSV stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def clear_csv_files(self):
        """Clear CSV files and recreate headers"""
        try:
            # Remove existing files
            if os.path.exists(self.frontend_csv_file):
                os.remove(self.frontend_csv_file)
            if os.path.exists(self.backend_csv_file):
                os.remove(self.backend_csv_file)
            
            # Recreate with headers
            self.ensure_headers()
            logging.info("CSV files cleared and recreated")
            
        except Exception as e:
            logging.error(f"Failed to clear CSV files: {e}")
    
    def export_csv_files(self, export_dir: str = None) -> Dict[str, str]:
        """Export CSV files to specified directory"""
        if export_dir is None:
            export_dir = os.path.join(self.log_dir, 'exports')
        
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        try:
            # Export frontend CSV
            if os.path.exists(self.frontend_csv_file):
                frontend_export = os.path.join(export_dir, f'frontend_logs_{timestamp}.csv')
                with open(self.frontend_csv_file, 'r', encoding='utf-8') as src, \
                     open(frontend_export, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                exported_files['frontend'] = frontend_export
            
            # Export backend CSV
            if os.path.exists(self.backend_csv_file):
                backend_export = os.path.join(export_dir, f'backend_logs_{timestamp}.csv')
                with open(self.backend_csv_file, 'r', encoding='utf-8') as src, \
                     open(backend_export, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                exported_files['backend'] = backend_export
                
        except Exception as e:
            logging.error(f"Failed to export CSV files: {e}")
            exported_files['error'] = str(e)
        
        return exported_files

# Global CSV logger instance
csv_logger = CSVLogger()

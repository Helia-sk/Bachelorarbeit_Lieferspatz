#!/usr/bin/env python3
"""
Separate Logging Dashboard Flask App
This runs independently from your main app to avoid logging interference
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Configure CORS for the dashboard
CORS(app, 
      origins=["http://localhost:5174", "http://localhost:3000"],
      methods=["GET", "POST", "OPTIONS"],
      allow_headers=["Content-Type"]
)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_logs.db')

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

@app.route('/')
def dashboard():
    """Main logging dashboard page"""
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User Interaction Logs Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
        <style>
            .log-entry { transition: all 0.3s ease; }
            .log-entry:hover { transform: translateX(5px); }
            .stats-card { transition: all 0.3s ease; }
            .stats-card:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <!-- Header -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <div class="space-y-6">
                    <div class="text-center">
                        <h1 class="text-3xl font-bold text-gray-800">📊 User Interaction Logs</h1>
                        <p class="text-gray-600 mt-2">Real-time monitoring dashboard for research purposes</p>
                    </div>
                    
                    <div class="space-y-4">
                        <!-- Export Section -->
                        <div>
                            <h3 class="text-lg font-semibold text-gray-700 mb-3 flex items-center">
                                <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium mr-2">📊</span>
                                Export Options
                            </h3>
                            
                            <!-- CSV Export Buttons - First Line -->
                            <div class="grid grid-cols-3 gap-4 mb-4">
                                <button onclick="exportFrontendLogsCSV()" class="bg-gradient-to-r from-blue-400 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    📱 Frontend CSV
                                </button>
                                <button onclick="exportBackendLogsCSV()" class="bg-gradient-to-r from-orange-400 to-orange-500 hover:from-orange-500 hover:to-orange-600 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    🖥️ Backend CSV
                                </button>
                                <button onclick="exportAllLogsCSV()" class="bg-gradient-to-r from-green-400 to-green-500 hover:from-green-500 hover:to-green-600 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    📥 All CSV
                                </button>
                            </div>
                            
                            <!-- JSON Export Buttons - Second Line -->
                            <div class="grid grid-cols-3 gap-4 mb-4">
                                <button onclick="exportFrontendLogsJSON()" class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    📱 Frontend JSON
                                </button>
                                <button onclick="exportBackendLogsJSON()" class="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    🖥️ Backend JSON
                                </button>
                                <button onclick="exportAllLogsJSON()" class="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    📥 All JSON
                                </button>
                            </div>
                            
                            <!-- Special Buttons - Third Line -->
                            <div class="grid grid-cols-1 gap-4">
                                <button onclick="resetLogs()" class="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-6 py-3 rounded-lg transition-all duration-200 text-sm font-medium shadow-md hover:shadow-lg transform hover:-translate-y-1">
                                    🔄 Reset All Logs
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
                <div class="stats-card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center">
                        <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Total Logs</p>
                            <p class="text-2xl font-semibold text-gray-900" id="totalLogs">0</p>
                            <p class="text-xs text-gray-500" id="logsBreakdown">Frontend: 0 | Backend: 0</p>
                        </div>
                    </div>
                </div>
                
                <div class="stats-card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center">
                        <div class="p-3 rounded-full bg-green-100 text-green-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Active Sessions</p>
                            <p class="text-2xl font-semibold text-gray-900" id="totalSessions">0</p>
                        </div>
                    </div>
                </div>
                
                <div class="stats-card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center">
                        <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Last 24h</p>
                            <p class="text-2xl font-semibold text-gray-900" id="recentActivity">0</p>
                        </div>
                    </div>
                </div>
                
                <div class="stats-card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center">
                        <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Live Updates</p>
                            <p class="text-2xl font-semibold text-gray-900" id="connectionStatus">🟢 Live</p>
                        </div>
                    </div>
                </div>
                
                <div class="stats-card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center">
                        <div class="p-3 rounded-full bg-indigo-100 text-indigo-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">CSV Logs</p>
                            <p class="text-2xl font-semibold text-gray-900" id="csvStats">0</p>
                            <p class="text-xs text-gray-500" id="csvBreakdown">Frontend: 0 | Backend: 0</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Filters and Search -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Search</label>
                        <input type="text" id="searchInput" placeholder="Search logs..." 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Event</label>
                        <select id="eventFilter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">All Events</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Schema</label>
                        <select id="schemaFilter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">All Schemas</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Session</label>
                        <select id="sessionFilter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">All Sessions</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Source</label>
                        <select id="sourceFilter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">All Sources</option>
                            <option value="frontend">Frontend</option>
                            <option value="backend">Backend</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Logs Table -->
            <div class="bg-white rounded-lg shadow-md overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Live Logs</h3>
                    <p class="text-sm text-gray-600">Real-time user interactions from your main application</p>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schema</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Session</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200" id="logsTableBody">
                            <!-- Logs will be populated here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            let logs = [];
            let filteredLogs = [];
            let socket = null;
            let stats = {};

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                fetchStats();
                fetchLogs();
                setupWebSocket();
                setupFilters();
            });

            // WebSocket connection
            function setupWebSocket() {
                try {
                    socket = io('http://localhost:5050');
                    
                    socket.on('connect', () => {
                        console.log('✅ Connected to logging server');
                        document.getElementById('connectionStatus').textContent = '🟢 Live';
                        document.getElementById('connectionStatus').className = 'text-2xl font-semibold text-green-600';
                    });

                    socket.on('disconnect', () => {
                        console.log('❌ Disconnected from logging server');
                        document.getElementById('connectionStatus').textContent = '🔴 Offline';
                        document.getElementById('connectionStatus').className = 'text-2xl font-semibold text-red-600';
                    });

                    socket.on('new_log', (log) => {
                        console.log('📝 New log received:', log);
                        addNewLog(log);
                        updateStats();
                    });

                    socket.on('logs_reset', () => {
                        console.log('🔄 Logs reset received');
                        logs = [];
                        filteredLogs = [];
                        renderLogs();
                        fetchStats();
                    });

                } catch (error) {
                    console.error('❌ WebSocket setup error:', error);
                }
            }

            // Fetch initial stats
            async function fetchStats() {
                try {
                    const response = await fetch('http://localhost:5050/api/logs/stats');
                    if (response.ok) {
                        stats = await response.json();
                        updateStatsDisplay();
                    }
                } catch (error) {
                    console.error('❌ Error fetching stats:', error);
                }
                
                // Fetch CSV stats
                try {
                    const csvResponse = await fetch('http://localhost:5050/api/logs/csv/stats');
                    if (csvResponse.ok) {
                        const csvStats = await csvResponse.json();
                        updateCSVStatsDisplay(csvStats.csv_stats);
                    }
                } catch (error) {
                    console.error('❌ Error fetching CSV stats:', error);
                }
            }

            // Fetch initial logs
            async function fetchLogs() {
                try {
                    const response = await fetch('http://localhost:5050/api/logs?limit=100');
                    if (response.ok) {
                        const data = await response.json();
                        logs = data.logs || [];
                        filteredLogs = [...logs];
                        renderLogs();
                        updateFilters();
                    }
                } catch (error) {
                    console.error('❌ Error fetching logs:', error);
                }
            }

            // Update stats display
            function updateStatsDisplay() {
                document.getElementById('totalLogs').textContent = stats.total_logs || 0;
                document.getElementById('totalSessions').textContent = stats.total_sessions || 0;
                document.getElementById('recentActivity').textContent = stats.recent_activity_24h || 0;
                
                // Update logs breakdown
                const frontendCount = logs.filter(log => log.log_type === 'frontend').length;
                const backendCount = logs.filter(log => log.log_type === 'backend').length;
                document.getElementById('logsBreakdown').textContent = `Frontend: ${frontendCount} | Backend: ${backendCount}`;
            }
            
            // Update CSV stats display
            function updateCSVStatsDisplay(csvStats) {
                const totalCSV = (csvStats.frontend_lines || 0) + (csvStats.backend_lines || 0);
                document.getElementById('csvStats').textContent = totalCSV;
                document.getElementById('csvBreakdown').textContent = `Frontend: ${csvStats.frontend_lines || 0} | Backend: ${csvStats.backend_lines || 0}`;
            }

            // Add new log to the list
            function addNewLog(log) {
                logs.unshift(log);
                if (logs.length > 1000) logs = logs.slice(0, 1000); // Keep only last 1000
                applyFilters();
            }

            // Update stats when new logs arrive
            function updateStats() {
                stats.total_logs = (stats.total_logs || 0) + 1;
                updateStatsDisplay();
            }

            // Setup filter event listeners
            function setupFilters() {
                document.getElementById('searchInput').addEventListener('input', applyFilters);
                document.getElementById('eventFilter').addEventListener('change', applyFilters);
                document.getElementById('schemaFilter').addEventListener('change', applyFilters);
                document.getElementById('sessionFilter').addEventListener('change', applyFilters);
                document.getElementById('sourceFilter').addEventListener('change', applyFilters);
            }

            // Apply filters
            function applyFilters() {
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                const selectedEvent = document.getElementById('eventFilter').value;
                const selectedSchema = document.getElementById('schemaFilter').value;
                const selectedSession = document.getElementById('sessionFilter').value;
                const selectedSource = document.getElementById('sourceFilter').value;

                filteredLogs = logs.filter(log => {
                    const matchesSearch = !searchTerm || 
                        log.event_name?.toLowerCase().includes(searchTerm) ||
                        log.schema_version?.toLowerCase().includes(searchTerm) ||
                        (log.details && JSON.stringify(log.details).toLowerCase().includes(searchTerm));
                    
                    const matchesEvent = !selectedEvent || log.event_name === selectedEvent;
                    const matchesSchema = !selectedSchema || log.schema_version === selectedSchema;
                    const matchesSession = !selectedSession || log.session_id === selectedSession;
                    
                    // Source filter logic
                    let matchesSource = true;
                    if (selectedSource === 'frontend') {
                        matchesSource = log.log_type === 'frontend';
                    } else if (selectedSource === 'backend') {
                        matchesSource = log.log_type === 'backend';
                    }

                    return matchesSearch && matchesEvent && matchesSchema && matchesSession && matchesSource;
                });

                renderLogs();
            }

            // Update filter options
            function updateFilters() {
                const events = [...new Set(logs.map(log => log.event_name))];
                const schemas = [...new Set(logs.map(log => log.schema_version))];
                const sessions = [...new Set(logs.map(log => log.session_id))];

                populateSelect('eventFilter', events);
                populateSelect('schemaFilter', schemas);
                populateSelect('sessionFilter', sessions);
            }

            function populateSelect(selectId, options) {
                const select = document.getElementById(selectId);
                const currentValue = select.value;
                
                // Keep the "All" option
                select.innerHTML = `<option value="">All ${selectId.replace('Filter', 's')}</option>`;
                
                options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option;
                    optionElement.textContent = option;
                    select.appendChild(optionElement);
                });
                
                select.value = currentValue;
            }

            // Render logs table
            function renderLogs() {
                const tbody = document.getElementById('logsTableBody');
                tbody.innerHTML = '';

                if (filteredLogs.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                                No logs found. Start interacting with your main application to see logs here.
                            </td>
                        </tr>
                    `;
                    return;
                }

                filteredLogs.forEach(log => {
                    const row = document.createElement('tr');
                    row.className = 'log-entry hover:bg-gray-50';
                    
                    const timestamp = new Date(log.timestamp).toLocaleString();
                    const eventClass = getEventClass(log.event_name);
                    const typeClass = getTypeClass(log.log_type);
                    
                    row.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${timestamp}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${eventClass}">
                                ${log.event_name}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${typeClass}">
                                ${log.log_type}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${log.schema_version || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${log.session_id ? log.session_id.substring(0, 8) + '...' : 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate">${log.route || 'N/A'}</td>
                    `;
                    
                    tbody.appendChild(row);
                });
            }

            // Get event color class
            function getEventClass(event) {
                const classes = {
                    // Frontend events
                    'click': 'bg-blue-100 text-blue-800',
                    'form_submit': 'bg-green-100 text-green-800',
                    'input_change': 'bg-yellow-100 text-yellow-800',
                    'page_view': 'bg-purple-100 text-purple-800',
                    'scroll': 'bg-gray-100 text-gray-800',
                    'window_resize': 'bg-indigo-100 text-indigo-800',
                    'error': 'bg-red-100 text-red-800',
                    'navigation': 'bg-pink-100 text-pink-800',
                    'button_click': 'bg-blue-100 text-blue-800',
                    // Backend events
                    'http_request': 'bg-orange-100 text-orange-800',
                    'http_response': 'bg-teal-100 text-teal-800',
                    'database_query': 'bg-cyan-100 text-cyan-800',
                    'file_operation': 'bg-lime-100 text-lime-800',
                    'login_attempt_result': 'bg-red-100 text-red-800'
                };
                return classes[event] || 'bg-gray-100 text-gray-800';
            }

            // Get type color class
            function getTypeClass(type) {
                const classes = {
                    'frontend': 'bg-blue-100 text-blue-800',
                    'backend': 'bg-orange-100 text-orange-800'
                };
                return classes[type] || 'bg-gray-100 text-gray-800';
            }

            // Export frontend logs as JSON
            async function exportFrontendLogsJSON() {
                try {
                    console.log('📱 Starting frontend logs JSON export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const frontendLogs = logsData.logs.filter(log => log.log_type === 'frontend');
                    
                    if (frontendLogs.length === 0) {
                        alert('⚠️ No frontend logs found to export');
                        return;
                    }
                    
                                         // Create and download JSON file
                     const blob = new Blob([JSON.stringify(frontendLogs, null, 2)], { type: 'application/json' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_frontend_session.json`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${frontendLogs.length} frontend logs as JSON successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting frontend logs as JSON:', error);
                    alert(`❌ Error exporting frontend logs as JSON: ${error.message}`);
                }
            }

            // Export frontend logs as CSV
            async function exportFrontendLogsCSV() {
                try {
                    console.log('📱 Starting frontend logs CSV export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const frontendLogs = logsData.logs.filter(log => log.log_type === 'frontend');
                    
                    if (frontendLogs.length === 0) {
                        alert('⚠️ No frontend logs found to export');
                        return;
                    }
                    
                    // Convert to CSV format
                    const csvContent = convertLogsToCSV(frontendLogs);
                    
                                         // Create and download CSV file
                     const blob = new Blob([csvContent], { type: 'text/csv' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_frontend_session.csv`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${frontendLogs.length} frontend logs as CSV successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting frontend logs as CSV:', error);
                    alert(`❌ Error exporting frontend logs as CSV: ${error.message}`);
                }
            }

            // Export backend logs as JSON
            async function exportBackendLogsJSON() {
                try {
                    console.log('🖥️ Starting backend logs JSON export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const backendLogs = logsData.logs.filter(log => log.log_type === 'backend');
                    
                    if (backendLogs.length === 0) {
                        alert('⚠️ No backend logs found to export');
                        return;
                    }
                    
                                         // Create and download JSON file
                     const blob = new Blob([JSON.stringify(backendLogs, null, 2)], { type: 'application/json' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_backend_session.json`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${backendLogs.length} backend logs as JSON successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting backend logs as JSON:', error);
                    alert(`❌ Error exporting backend logs as JSON: ${error.message}`);
                }
            }

            // Export backend logs as CSV
            async function exportBackendLogsCSV() {
                try {
                    console.log('🖥️ Starting backend logs CSV export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const backendLogs = logsData.logs.filter(log => log.log_type === 'backend');
                    
                    if (backendLogs.length === 0) {
                        alert('⚠️ No backend logs found to export');
                        return;
                    }
                    
                    // Convert to CSV format
                    const csvContent = convertLogsToCSV(backendLogs);
                    
                                         // Create and download CSV file
                     const blob = new Blob([csvContent], { type: 'text/csv' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_backend_session.csv`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${backendLogs.length} backend logs as CSV successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting backend logs as CSV:', error);
                    alert(`❌ Error exporting backend logs as CSV: ${error.message}`);
                }
            }

            // Export all logs as JSON
            async function exportAllLogsJSON() {
                try {
                    console.log('📥 Starting all logs JSON export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const exportData = logsData.logs;
                    
                    if (exportData.length === 0) {
                        alert('⚠️ No logs found to export');
                        return;
                    }
                    
                                         // Create and download JSON file
                     const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_all_combined.json`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${exportData.length} logs as JSON successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting all logs as JSON:', error);
                    alert(`❌ Error exporting all logs as JSON: ${error.message}`);
                }
            }

            // Export all logs as CSV
            async function exportAllLogsCSV() {
                try {
                    console.log('📥 Starting all logs CSV export...');
                    const logsResponse = await fetch('http://localhost:5050/api/logs?limit=10000');
                    if (!logsResponse.ok) {
                        throw new Error(`Failed to fetch logs: ${logsResponse.status}`);
                    }
                    
                    const logsData = await logsResponse.json();
                    const exportData = logsData.logs;
                    
                    if (exportData.length === 0) {
                        alert('⚠️ No logs found to export');
                        return;
                    }
                    
                    // Convert to CSV format
                    const csvContent = convertLogsToCSV(exportData);
                    
                                         // Create and download CSV file
                     const blob = new Blob([csvContent], { type: 'text/csv' });
                     const url = window.URL.createObjectURL(blob);
                     const link = document.createElement('a');
                     link.href = url;
                     link.download = `logs_all_combined.csv`;
                     document.body.appendChild(link);
                     link.click();
                     document.body.removeChild(link);
                     window.URL.revokeObjectURL(url);
                    
                    alert(`✅ Exported ${exportData.length} logs as CSV successfully!`);
                } catch (error) {
                    console.error('❌ Error exporting all logs as CSV:', error);
                    alert(`❌ Error exporting all logs as CSV: ${error.message}`);
                }
            }

            // Helper function to convert logs to CSV format
            function convertLogsToCSV(logs) {
                if (logs.length === 0) return '';
                
                // Define CSV headers based on the first log entry
                const headers = [
                    'id',
                    'timestamp',
                    'log_type',
                    'schema_version',
                    'event_name',
                    'session_id',
                    'attempt_id',
                    'browser_id',
                    'route',
                    'details'
                ];
                
                // Create CSV header row
                const csvRows = [headers.join(',')];
                
                // Convert each log to CSV row
                logs.forEach(log => {
                    const row = headers.map(header => {
                        let value = log[header] || '';
                        
                        // Handle special cases
                        if (header === 'details' && typeof value === 'object') {
                            value = JSON.stringify(value);
                        }
                        
                        // Escape commas and quotes in CSV
                        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                            value = `"${value.replace(/"/g, '""')}"`;
                        }
                        
                        return value;
                    });
                    
                    csvRows.push(row.join(','));
                });
                
                return csvRows.join('\\n');
            }



            // Reset logs
            async function resetLogs() {
                if (confirm('Are you sure you want to reset all logs? This action cannot be undone.')) {
                    try {
                        console.log('🔄 Starting logs reset...');
                        const response = await fetch('http://localhost:5050/api/logs/reset', { 
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        const data = await response.json();
                        console.log('🔄 Reset response:', data);
                        
                        logs = [];
                        filteredLogs = [];
                        renderLogs();
                        fetchStats();
                        alert('✅ All logs have been reset successfully!');
                    } catch (error) {
                        console.error('❌ Error resetting logs:', error);
                        alert(`❌ Error resetting logs: ${error.message}`);
                    }
                }
            }
        </script>
    </body>
    </html>
    '''
    return html

if __name__ == "__main__":
    print("🚀 Starting Logging Dashboard on port 5001...")
    print("📊 Dashboard available at: http://localhost:5001")
    print("🔗 Make sure your main Flask app is running on port 5050")
    app.run(debug=True, host='localhost', port=5001)

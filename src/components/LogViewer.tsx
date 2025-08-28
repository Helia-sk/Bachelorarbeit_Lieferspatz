import React, { useState, useEffect, useRef } from 'react';
import { UserInteraction } from '../utils/logger';
import { io, Socket } from 'socket.io-client';

interface LogViewerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface LogStats {
  total_logs: number;
  total_sessions: number;
  recent_activity_24h: number;
  actions_breakdown: Record<string, number>;
  components_breakdown: Record<string, number>;
}

const LogViewer: React.FC<LogViewerProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<UserInteraction[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<UserInteraction[]>([]);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [selectedComponent, setSelectedComponent] = useState<string>('');
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  // Initialize socket connection
  useEffect(() => {
    if (isOpen) {
      console.log('🔌 Attempting to connect to logging server...');
      setConnectionStatus('connecting');
      
             const newSocket = io('http://localhost:5050', {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: 5
      });
      
      setSocket(newSocket);

      newSocket.on('connect', () => {
        console.log('✅ Connected to logging server');
        setConnectionStatus('connected');
      });

      newSocket.on('connect_error', (error) => {
        console.error('❌ Connection error:', error);
        setConnectionStatus('error');
      });

      newSocket.on('disconnect', (reason) => {
        console.log('🔌 Disconnected from logging server:', reason);
        setConnectionStatus('disconnected');
      });

      newSocket.on('new_log', (log: UserInteraction) => {
        console.log('📝 Received new log:', log);
        setLogs(prev => [log, ...prev]);
        if (autoScroll) {
          scrollToBottom();
        }
      });

      newSocket.on('logs_reset', () => {
        console.log('🔄 Logs reset received');
        setLogs([]);
        setFilteredLogs([]);
        fetchStats();
      });

      newSocket.on('logs_buffer', (data: { logs: UserInteraction[] }) => {
        console.log('📦 Received logs buffer:', data.logs.length, 'logs');
        setLogs(data.logs);
        setFilteredLogs(data.logs);
      });

      return () => {
        console.log('🔌 Cleaning up socket connection');
        newSocket.close();
      };
    }
  }, [isOpen]);

  // Fetch initial logs and stats
  useEffect(() => {
    if (isOpen) {
      console.log('📊 Fetching initial logs and stats...');
      fetchLogs();
      fetchStats();
      // Get current session ID from localStorage or generate one
      const sessionId = localStorage.getItem('currentSessionId') || `session_${Date.now()}`;
      setCurrentSessionId(sessionId);
      localStorage.setItem('currentSessionId', sessionId);
    }
  }, [isOpen]);

  // Filter logs when search or filters change
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.event_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.component?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.url?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.route?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.event_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(log.details).toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedAction) {
      filtered = filtered.filter(log => log.event_name === selectedAction);
    }

    if (selectedComponent) {
      filtered = filtered.filter(log => log.component === selectedComponent);
    }

    if (selectedSession) {
      filtered = filtered.filter(log => log.session_id === selectedSession);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, selectedAction, selectedComponent, selectedSession]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      console.log('📡 Fetching logs from API...');
             const response = await fetch('/api/logs?limit=100');
      console.log('📡 API response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📡 Received logs data:', data);
      setLogs(data.logs || []);
      setFilteredLogs(data.logs || []);
    } catch (error) {
      console.error('❌ Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      console.log('📊 Fetching stats...');
             const response = await fetch('/api/logs/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('📊 Received stats:', data);
      setStats(data);
    } catch (error) {
      console.error('❌ Error fetching stats:', error);
    }
  };

  const resetLogs = async () => {
    if (window.confirm('Are you sure you want to reset all logs? This action cannot be undone.')) {
      try {
                 await fetch('/api/logs/reset', { method: 'POST' });
        setLogs([]);
        setFilteredLogs([]);
        fetchStats();
      } catch (error) {
        console.error('❌ Error resetting logs:', error);
      }
    }
  };

  const exportLogs = async () => {
    try {
             const response = await fetch('/api/logs/export');
      const data = await response.json();
      
      // Create download link
      const link = document.createElement('a');
             link.href = `/${data.filename}`;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('❌ Error exporting logs:', error);
    }
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp: string | undefined) => {
    if (!timestamp) return 'Unknown time';
    return new Date(timestamp).toLocaleString();
  };

  const getUniqueValues = (field: keyof UserInteraction): string[] => {
    const values = new Set(logs.map(log => log[field]).filter((value): value is string => typeof value === 'string'));
    return Array.from(values);
  };

  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      'click': 'bg-blue-100 text-blue-800',
      'form_submit': 'bg-green-100 text-green-800',
      'input_change': 'bg-yellow-100 text-yellow-800',
      'page_view': 'bg-purple-100 text-purple-800',
      'scroll': 'bg-gray-100 text-gray-800',
      'window_resize': 'bg-indigo-100 text-indigo-800',
      'error': 'bg-red-100 text-red-800',
      'navigation': 'bg-pink-100 text-pink-800'
    };
    return colors[action] || 'bg-gray-100 text-gray-800';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-11/12 h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold">User Interaction Logs</h2>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' :
                connectionStatus === 'connecting' ? 'bg-yellow-500' :
                connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-500'
              }`}></div>
              <span className="text-sm text-gray-600 capitalize">{connectionStatus}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchLogs}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Refresh
            </button>
            <button
              onClick={exportLogs}
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Export
            </button>
            <button
              onClick={resetLogs}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Reset All
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        {stats && (
          <div className="bg-gray-50 p-4 border-b">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              <div className="text-center">
                <div className="font-bold text-lg">{stats.total_logs}</div>
                <div className="text-gray-600">Total Logs</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{stats.total_sessions}</div>
                <div className="text-gray-600">Sessions</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{stats.recent_activity_24h}</div>
                <div className="text-gray-600">Last 24h</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{Object.keys(stats.actions_breakdown).length}</div>
                <div className="text-gray-600">Actions</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{Object.keys(stats.components_breakdown).length}</div>
                <div className="text-gray-600">Components</div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="p-4 border-b bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border rounded"
            />
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="px-3 py-2 border rounded"
            >
              <option value="">All Actions</option>
              {getUniqueValues('event_name').map((action: string) => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
            <select
              value={selectedComponent}
              onChange={(e) => setSelectedComponent(e.target.value)}
              className="px-3 py-2 border rounded"
            >
              <option value="">All Components</option>
              {getUniqueValues('component').map((component: string) => (
                <option key={component} value={component}>{component}</option>
              ))}
            </select>
            <select
              value={selectedSession}
              onChange={(e) => setSelectedSession(e.target.value)}
              className="px-3 py-2 border rounded"
            >
              <option value="">All Sessions</option>
              <option value={currentSessionId}>Current Session</option>
              {getUniqueValues('session_id').map((sessionId: string) => (
                <option key={sessionId} value={sessionId}>{sessionId.substring(0, 20)}...</option>
              ))}
            </select>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              Auto-scroll
            </label>
          </div>
        </div>

        {/* Logs Display */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="text-center py-8">Loading logs...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-4">No logs found</div>
              <div className="text-sm text-gray-400">
                Try interacting with the website (clicking, scrolling, etc.) and then refresh
              </div>
              <div className="text-xs text-gray-300 mt-2">
                Connection: {connectionStatus} | Logs in state: {logs.length}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionColor(log.event_name || '')}`}>
                          {log.event_name}
                        </span>
                        <span className="text-sm text-gray-600">{log.component}</span>
                        <span className="text-xs text-gray-500">{formatTimestamp(log.timestamp || log.event_time || '')}</span>
                      </div>
                      
                      <div className="text-sm text-gray-700 mb-2">
                        <strong>URL:</strong> {log.url}
                      </div>
                      
                      {log.userId && (
                        <div className="text-sm text-gray-700 mb-2">
                          <strong>User ID:</strong> {log.userId}
                        </div>
                      )}
                      
                      <div className="text-sm text-gray-700 mb-2">
                        <strong>Session:</strong> {log.session_id?.substring(0, 20) || 'Unknown'}...
                      </div>
                      
                      {Object.keys(log.details).length > 0 && (
                        <div className="text-sm text-gray-700">
                          <strong>Details:</strong>
                          <pre className="mt-1 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                    
                    <div className="text-xs text-gray-500 text-right ml-4">
                      <div>Viewport: {log.viewport.width}×{log.viewport.height}</div>
                      <div className="mt-1">
                        {(log.session_id === currentSessionId) && (
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            Current
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 text-sm text-gray-600">
          Showing {filteredLogs.length} of {logs.length} logs
          {selectedAction && ` • Action: ${selectedAction}`}
          {selectedComponent && ` • Component: ${selectedComponent}`}
          {selectedSession && ` • Session: ${selectedSession.substring(0, 20)}...`}
        </div>
      </div>
    </div>
  );
};

export default LogViewer;

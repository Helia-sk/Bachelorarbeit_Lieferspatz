import React, { useEffect, useState } from 'react';
import apiClient from '../api';

const LogsViewer: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/logs/');
      setLogs(res.data || []);
    } catch (err) {
      setError('Failed to load logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Frontend Logs</h1>
        <div>
          <button
            className="bg-orange-500 text-white px-3 py-1 rounded-md"
            onClick={fetchLogs}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded-md mb-4">{error}</div>}

      <div className="space-y-4">
        {loading && <div>Loading...</div>}
        {!loading && logs.length === 0 && <div className="text-gray-500">No logs yet.</div>}

        {logs.map((l) => (
          <div key={l.id} className="p-4 bg-white rounded shadow-sm">
            <div className="text-sm text-gray-600">{new Date(l.timestamp).toLocaleString()}</div>
            <div className="font-medium mt-1">{l.action}</div>
            <pre className="mt-2 text-xs text-gray-700 overflow-auto max-h-40">{JSON.stringify(JSON.parse(l.description || '{}'), null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LogsViewer;

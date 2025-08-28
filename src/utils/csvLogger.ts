export interface CSVLogEntry {
  timestamp: string;
  event: string;
  session_id: string;
  route: string;
  method?: string;
  status_code?: string;
  user_id?: string;
  ip_address?: string;
  component?: string;
  action?: string;
  browser_id?: string;
  attempt_id?: string;
  details?: any;
}

export class CSVLogger {
  private csvBuffer: CSVLogEntry[] = [];
  private readonly bufferSize = 10;
  private readonly csvHeaders = [
    'timestamp',
    'event',
    'session_id',
    'route',
    'method',
    'status_code',
    'user_id',
    'ip_address',
    'component',
    'action',
    'browser_id',
    'attempt_id',
    'details'
  ];

  /**
   * Log data to CSV format
   */
  logToCSV(data: any): void {
    const csvEntry = this.formatToCSVEntry(data);
    this.csvBuffer.push(csvEntry);
    
    // Flush buffer when it's full
    if (this.csvBuffer.length >= this.bufferSize) {
      this.flush();
    }
  }

  /**
   * Format data to CSV entry
   */
  private formatToCSVEntry(data: any): CSVLogEntry {
    return {
      timestamp: data.timestamp || new Date().toISOString(),
      event: data.event || data.action || 'unknown',
      session_id: data.session_id || data.sessionId || 'unknown',
      route: data.route || data.url || 'unknown',
      method: data.details?.method || data.method || '',
      status_code: data.details?.status_code || data.status_code || '',
      user_id: data.details?.user_id || data.userId || data.browser_id || '',
      ip_address: data.details?.ip_address || data.ip_address || '',
      component: data.component || data.details?.component || '',
      action: data.action || data.event || '',
      browser_id: data.browser_id || data.userId || '',
      attempt_id: data.attempt_id || '',
      details: data.details ? JSON.stringify(data.details) : ''
    };
  }

  /**
   * Flush the buffer and send to backend
   */
  async flush(): Promise<void> {
    if (this.csvBuffer.length === 0) return;

    try {
      const csvData = this.csvBuffer.map(entry => 
        this.csvHeaders.map(header => entry[header as keyof CSVLogEntry] || '').join(',')
      );

      // Send CSV data to backend
      await this.sendCSVLogs(csvData);
      
      // Clear buffer after successful send
      this.csvBuffer = [];
    } catch (error) {
      console.error('Failed to flush CSV logs:', error);
    }
  }

  /**
   * Send CSV logs to backend
   */
  private async sendCSVLogs(csvLines: string[]): Promise<void> {
    try {
      const response = await fetch('/api/logs/csv', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          csv_data: csvLines,
          headers: this.csvHeaders
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error sending CSV logs:', error);
      throw error;
    }
  }

  /**
   * Force flush and clear buffer
   */
  async forceFlush(): Promise<void> {
    await this.flush();
  }

  /**
   * Get current buffer size
   */
  getBufferSize(): number {
    return this.csvBuffer.length;
  }

  /**
   * Clear buffer without sending
   */
  clearBuffer(): void {
    this.csvBuffer = [];
  }
}

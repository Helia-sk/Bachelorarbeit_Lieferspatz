# User Interaction Logging System

This project includes a comprehensive logging system that captures all user interactions with the frontend in real-time, perfect for research and user behavior analysis.

## Features

- **Automatic Capture**: Automatically logs clicks, form submissions, input changes, page views, scroll events, and window resizes
- **Real-time Viewing**: Live log updates with WebSocket connection
- **JSON Output**: All logs are stored in JSON format with timestamps
- **Research Ready**: Filter, search, and export logs for analysis
- **Session Tracking**: Track user sessions and interactions across the application
- **Reset Capability**: Clear all logs when needed
- **Performance Optimized**: Batched logging with configurable flush intervals

## Architecture

```
Frontend (React) → Logger Service → Backend API (Flask) → SQLite DB + JSON Files
                                    ↓
                              Real-time Viewer (WebSocket)
```

## Setup Instructions

### 1. Backend Setup

Navigate to the Backend directory and install dependencies:

```bash
cd Backend
pip install -r logging_requirements.txt
```

### 2. Start the Logging API

```bash
python start_logging_api.py
```

The logging server will start on `http://localhost:5001`

### 3. Frontend Integration

The logging system is already integrated into your React application. The `LogToggle` component provides a floating button (bottom-right corner) to access the log viewer.

## Usage

### Viewing Logs

1. Click the blue floating button (📄) in the bottom-right corner of your application
2. The log viewer will open showing real-time user interactions
3. Use filters to narrow down specific actions, components, or sessions
4. Search through log details with the search bar

### Log Types Captured

- **Clicks**: Button clicks, link clicks, element interactions
- **Form Submissions**: Form data and submission details
- **Input Changes**: Text input, textarea, and select changes
- **Page Views**: Navigation between pages
- **Scroll Events**: User scrolling behavior
- **Window Resize**: Viewport changes
- **Custom Events**: Programmatically logged interactions

### Filtering and Search

- **Action Filter**: Filter by specific actions (click, form_submit, etc.)
- **Component Filter**: Filter by HTML elements or components
- **Session Filter**: View logs from specific user sessions
- **Search**: Full-text search across all log fields
- **Time-based**: View logs from specific time periods

### Export and Reset

- **Export**: Download all logs as JSON file for external analysis
- **Reset**: Clear all logs (use with caution)
- **Refresh**: Manually refresh log data

## API Endpoints

### POST `/api/logs`
Receive logs from frontend

### GET `/api/logs`
Retrieve logs with filtering options:
- `?limit=100` - Number of logs to return
- `?offset=0` - Pagination offset
- `?action=click` - Filter by action
- `?component=button` - Filter by component
- `?session_id=xxx` - Filter by session
- `?user_id=xxx` - Filter by user

### GET `/api/logs/stats`
Get logging statistics and breakdowns

### POST `/api/logs/reset`
Reset all logs

### GET `/api/logs/export`
Export logs as JSON file

## Log Data Structure

Each log entry contains:

```json
{
  "id": "unique_log_id",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "userId": "optional_user_id",
  "sessionId": "unique_session_id",
  "action": "click|form_submit|input_change|page_view|scroll|window_resize",
  "component": "button|form|input|navigation|document|window",
  "details": {
    "buttonText": "Click me",
    "buttonId": "submit-btn",
    "x": 150,
    "y": 200
  },
  "url": "https://yourapp.com/page",
  "userAgent": "Mozilla/5.0...",
  "viewport": {
    "width": 1920,
    "height": 1080
  }
}
```

## Custom Logging

You can manually log custom interactions:

```typescript
import { userLogger } from './utils/logger';

// Log custom button click
userLogger.logButtonClick('Custom Action', 'custom-btn', { 
  customData: 'value' 
});

// Log navigation
userLogger.logNavigation('/home', '/profile', 'button');

// Log errors
userLogger.logError(new Error('Something went wrong'), 'payment-form');

// Log performance metrics
userLogger.logPerformance('page_load', 1200, 'ms');
```

## Configuration

### Logger Settings

The logger can be configured in `src/utils/logger.ts`:

- `batchSize`: Number of logs to batch before sending (default: 10)
- `flushInterval`: Auto-flush interval in milliseconds (default: 5000)
- `isEnabled`: Enable/disable logging globally

### Backend Settings

Configure in `Backend/logging_api.py`:

- `MAX_LOGS_IN_MEMORY`: Maximum logs kept in memory (default: 1000)
- `LOG_FILE`: JSON backup file path
- `DB_FILE`: SQLite database file path

## Research Use Cases

This logging system is perfect for:

- **User Experience Research**: Track how users navigate your application
- **A/B Testing**: Compare user behavior across different versions
- **Performance Analysis**: Monitor user interaction patterns
- **Error Tracking**: Identify where users encounter issues
- **Conversion Funnel Analysis**: Track user journey through forms and actions
- **Accessibility Research**: Monitor how users interact with different elements

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check if the backend server is running on port 5001
2. **WebSocket connection failed**: Ensure CORS is properly configured
3. **Database errors**: Check file permissions for the SQLite database
4. **Performance issues**: Reduce batch size or increase flush interval

### Debug Mode

Enable debug logging in the browser console:

```typescript
// Enable debug mode
userLogger.enable();

// Check queue status
console.log('Queue size:', userLogger.getQueueSize());
console.log('Session ID:', userLogger.getCurrentSessionId());
```

## Security Considerations

- **Sensitive Data**: Passwords and sensitive form data are automatically masked
- **User Privacy**: Consider GDPR compliance when logging user interactions
- **Data Retention**: Implement automatic log cleanup for production use
- **Access Control**: Restrict log access to authorized personnel only

## Performance Impact

- **Minimal Overhead**: Logging is asynchronous and batched
- **Memory Efficient**: Configurable buffer sizes prevent memory bloat
- **Network Optimized**: Batched requests reduce API calls
- **Graceful Degradation**: Logging failures don't affect application functionality

## Support

For issues or questions about the logging system:

1. Check the browser console for error messages
2. Verify the backend server is running
3. Check network requests in browser dev tools
4. Review the log files in the Backend directory

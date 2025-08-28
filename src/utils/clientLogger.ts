import apiClient from '../api';

type LogPayload = {
  action: string;
  details?: any;
  url?: string;
  userAgent?: string;
  timestamp?: string;
};

export const logEvent = async (action: string, details?: any) => {
  const payload: LogPayload = {
    action,
    details,
    url: window.location.pathname,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
  };

  try {
    const body = JSON.stringify(payload);

    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: 'application/json' });
      // Use absolute backend path set in apiClient.baseURL
      const beaconUrl = new URL('/api/logs/', window.location.origin).toString();
      navigator.sendBeacon(beaconUrl, blob);
      return;
    }

    await apiClient.post('/api/logs/', payload, {
      headers: { 'Content-Type': 'application/json' },
      withCredentials: true,
    });
  } catch (err) {
    // swallow errors to avoid breaking UX
    // console.debug('Failed to send client log', err);
  }
};

export default logEvent;

import { CSVLogger } from './csvLogger';

interface UserInteraction {
  id: string;
  timestamp: string;
  event_name: string;
  attempt_id: string;
  session_id: string;
  browser_id: string;
  route: string;
  submit_trigger: string;
  client_validation_passed: boolean;
  username_length: number;
  password_length: number;
  autofill_used: boolean;
  caps_lock_on: boolean;
  perf: {
    submit_latency_ms: number;
  };
  event_time: string;
  app_version: string;
  schema_version: string;
  url: string;
  userAgent: string;
  viewport: {
    width: number;
    height: number;
  };
  // Input change specific fields
  inputName?: string;
  inputType?: string;
  inputValue?: string;
  inputId?: string;
  finalValueLength?: number;
  // System noise detection
  system_noise?: boolean;
  noise_reason?: string;
  // Component information
  component?: string;
  // User identification
  userId?: string;
  // Form submission specific - field presence mapping
  field_presence_map?: Record<string, boolean>;
  // All event-specific details consolidated
  details: Record<string, any>;
}

class UserInteractionLogger {
  private sessionId: string;
  private userId?: string;
  private isEnabled: boolean = true;
  private batchSize: number = 10;
  private logQueue: UserInteraction[] = [];
  private flushInterval: number = 5000; // 5 seconds
  private flushTimer?: NodeJS.Timeout;
  
  // Debounced input logging
  private inputChangeTimers: Map<string, NodeJS.Timeout> = new Map();
  private inputChangeValues: Map<string, { value: string; fieldName: string }> = new Map();
  
  // System noise configuration
  private logSystemNoise: boolean = true;  // Whether to log system noise at all
  private filterSystemNoise: boolean = true; // Whether to filter from user journey view
  private strictBusinessAPIFiltering: boolean = true; // Only log business API calls
  
  // CSV Logger for dual format logging
  private csvLogger: CSVLogger = new CSVLogger();

  constructor() {
    console.log('🚀 UserInteractionLogger initializing...');
    this.sessionId = this.generateSessionId();
    console.log('📝 Session ID:', this.sessionId);
    this.startAutoFlush();
    this.setupGlobalListeners();
    console.log('✅ UserInteractionLogger initialized successfully');
  }

  /**
   * Debounced input change logging - only logs after user stops typing
   */
  private debouncedInputChange(target: HTMLInputElement): void {
    const fieldKey = `${target.id || target.name || target.tagName}_${target.type}`;
    
    // Clear existing timer for this field
    if (this.inputChangeTimers.has(fieldKey)) {
      clearTimeout(this.inputChangeTimers.get(fieldKey)!);
    }
    
    // Store the current value and field name
    this.inputChangeValues.set(fieldKey, {
      value: target.value,
      fieldName: target.name || target.id || target.tagName
    });
    
    // Set new timer (500ms delay)
    const timer = setTimeout(() => {
      this.logDebouncedInputChange(fieldKey);
    }, 500);
    
    this.inputChangeTimers.set(fieldKey, timer);
  }

  /**
   * Log input change when debounce timer expires
   */
  private logDebouncedInputChange(fieldKey: string): void {
    const inputData = this.inputChangeValues.get(fieldKey);
    if (!inputData) return;
    
    // Get the target element to get additional context
    const target = document.querySelector(`[name="${inputData.fieldName}"], [id="${inputData.fieldName}"]`) as HTMLInputElement;
    if (!target) return;
    
    this.logInteraction('input_change', {
      trigger: 'debounced_input',
      inputName: inputData.fieldName,
      inputType: target.type,
      inputValue: target.type === 'password' ? '[HIDDEN]' : inputData.value.substring(0, 100),
      inputId: target.id,
      finalValueLength: inputData.value.length,
      schema_version: 'input_change.v1'
    });
    
    // Clean up
    this.inputChangeValues.delete(fieldKey);
    this.inputChangeTimers.delete(fieldKey);
  }

  /**
   * Log input change immediately when user leaves the field (blur)
   */
  private logInputChangeOnBlur(target: HTMLInputElement): void {
    const fieldKey = `${target.id || target.name || target.tagName}_${target.type}`;
    
    // Clear any pending debounced timer
    if (this.inputChangeTimers.has(fieldKey)) {
      clearTimeout(this.inputChangeTimers.get(fieldKey)!);
      this.inputChangeTimers.delete(fieldKey);
    }
    
    // Get stored value or use current value
    const storedData = this.inputChangeValues.get(fieldKey);
    const finalValue = storedData?.value || target.value;
    
    this.logInteraction('input_change', {
      trigger: 'blur',
      inputName: target.name || target.id || target.tagName,
      inputType: target.type,
      inputValue: target.type === 'password' ? '[HIDDEN]' : finalValue.substring(0, 100),
      inputId: target.id,
      finalValueLength: finalValue.length,
      schema_version: 'input_change.v1'
    });
    
    // Clean up
    this.inputChangeValues.delete(fieldKey);
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalListeners(): void {
    // Capture page views
    this.logPageView();

    // Capture navigation
    window.addEventListener('popstate', () => this.logPageView());
    
    // Capture clicks
            document.addEventListener('click', (e) => {
          const target = e.target as HTMLElement;
          if (target) {
            console.log('🖱️ Click detected on:', target.tagName, target.textContent?.trim());
            this.logInteraction('click', {
              trigger: 'click',
              text: target.textContent?.trim() || '',
              className: target.className,
              id: target.id,
              tagName: target.tagName,
              x: e.clientX,
              y: e.clientY,
              schema_version: 'click.v1'
            });
          }
        });

    // Capture form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target as HTMLFormElement;
      
      // Create field presence map - tracks which fields were filled vs empty
      const fieldPresenceMap: Record<string, boolean> = {};
      Array.from(form.elements).forEach(el => {
        if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement) {
          const fieldName = el.name || el.id || el.tagName.toLowerCase();
          if (fieldName) {
            // Check if field has a value (filled by user)
            let hasValue = false;
            if (el instanceof HTMLInputElement) {
              if (el.type === 'checkbox' || el.type === 'radio') {
                hasValue = el.checked;
              } else {
                hasValue = el.value.trim().length > 0;
              }
            } else if (el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement) {
              hasValue = el.value.trim().length > 0;
            }
            fieldPresenceMap[fieldName] = hasValue;
          }
        }
      });
      
      this.logInteraction('form_submit', {
        trigger: 'submit',
        formId: form.id,
        formAction: form.action,
        formMethod: form.method,
        formElements: Array.from(form.elements).map(el => ({
          name: (el as HTMLInputElement).name,
          type: (el as HTMLInputElement).type,
          required: (el as HTMLInputElement).required
        })),
        field_presence_map: fieldPresenceMap,
        schema_version: 'form_submit.v2'
      });
    });

    // Capture input changes with debouncing
    document.addEventListener('input', (e) => {
      const target = e.target as HTMLInputElement;
      if (target && ['input', 'textarea', 'select'].includes(target.tagName.toLowerCase())) {
        this.debouncedInputChange(target);
      }
    });

    // Capture input blur events for immediate logging
    document.addEventListener('blur', (e) => {
      const target = e.target as HTMLInputElement;
      if (target && ['input', 'textarea', 'select'].includes(target.tagName.toLowerCase())) {
        this.logInputChangeOnBlur(target);
      }
    }, true);

    // Capture scroll events (throttled)
    let scrollTimeout: NodeJS.Timeout;
    document.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.logInteraction('scroll', {
          trigger: 'scroll',
          scrollX: window.scrollX,
          scrollY: window.scrollY,
          scrollHeight: document.documentElement.scrollHeight,
          clientHeight: document.documentElement.clientHeight,
          schema_version: 'scroll.v1'
        });
      }, 100);
    });

    // Capture window resize
    let resizeTimeout: NodeJS.Timeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        this.logInteraction('window_resize', {
          trigger: 'resize',
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          outerWidth: window.outerWidth,
          outerHeight: window.outerHeight,
          schema_version: 'window_resize.v1'
        });
      }, 100);
    });
  }

  private logPageView(): void {
    this.logInteraction('page_view', {
      trigger: 'navigation',
      pathname: window.location.pathname,
      search: window.location.search,
      hash: window.location.hash,
      referrer: document.referrer,
      schema_version: 'page_view.v1'
    });
  }

  public logInteraction(event: string, details: Record<string, any> = {}): void {
    if (!this.isEnabled) return;

    // Check if this is system noise using enhanced detection
    const noiseCheck = this.isSystemNoiseEnhanced(event, details);
    
    // If it's system noise and we're configured to skip it, return early
    if (noiseCheck.isNoise && !this.logSystemNoise) {
      return;
    }
    
    // If it's system noise, we can either:
    // 1. Skip logging entirely (uncomment next line)
    // if (noiseCheck.isNoise) return;
    
    // 2. Log but flag as system noise (current approach)
    const interaction: UserInteraction = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      event_name: event,
      attempt_id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      session_id: this.sessionId,
      browser_id: this.userId || 'anonymous',
      route: window.location.pathname,
      submit_trigger: details.trigger || 'unknown',
      client_validation_passed: details.validation !== false,
      username_length: details.username?.length || 0,
      password_length: details.password?.length || 0,
      autofill_used: details.autofill || false,
      caps_lock_on: details.capsLock || false,
      perf: {
        submit_latency_ms: details.latency || 0
      },
      event_time: new Date().toISOString(),
      app_version: 'web-1.4.2',
      schema_version: details.schema_version || 'frontend.v1',
      // Additional context
      url: window.location.href,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      // Input change specific fields
      inputName: details.inputName,
      inputType: details.inputType,
      inputValue: details.inputValue,
      inputId: details.inputId,
      finalValueLength: details.finalValueLength,
      // System noise detection
      system_noise: noiseCheck.isNoise,
      noise_reason: noiseCheck.reason,
      // Component information
      component: details.component || 'unknown',
      // User identification
      userId: this.userId,
      // Form submission specific - field presence mapping
      field_presence_map: details.field_presence_map,
      // All event-specific details consolidated
      details: details
    };

    console.log('📝 Logging interaction:', { event, details });
    this.logQueue.push(interaction);
    console.log('📊 Queue size:', this.logQueue.length);
    
    // Dual logging: Also log to CSV format
    this.csvLogger.logToCSV(interaction);
    
    // Flush immediately if queue is full
    if (this.logQueue.length >= this.batchSize) {
      console.log('🚀 Flushing logs (queue full)');
      this.flushLogs();
    }
  }

  public setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Clean up timers and stored values to prevent memory leaks
   */
  public cleanup(): void {
    // Clear all pending input change timers
    this.inputChangeTimers.forEach(timer => clearTimeout(timer));
    this.inputChangeTimers.clear();
    this.inputChangeValues.clear();
    
    // Clear flush timer
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
    }
  }

  /**
   * Detect if an interaction is system noise (not user intent)
   */
  private isSystemNoise(event: string, details: Record<string, any>): { isNoise: boolean; reason?: string } {
    // CORS preflight OPTIONS requests
    if (event === 'http_request' && details.method === 'OPTIONS') {
      return { isNoise: true, reason: 'cors_preflight' };
    }

    // 308 redirects
    if (event === 'navigation' && details.statusCode === 308) {
      return { isNoise: true, reason: 'permanent_redirect' };
    }

    // 301 redirects (also system noise)
    if (event === 'navigation' && details.statusCode === 301) {
      return { isNoise: true, reason: 'moved_permanently' };
    }

    // 302 redirects (temporary redirects)
    if (event === 'navigation' && details.statusCode === 302) {
      return { isNoise: true, reason: 'temporary_redirect' };
    }

    // Browser-initiated requests (not user intent)
    if (event === 'http_request' && details.trigger === 'browser') {
      return { isNoise: true, reason: 'browser_initiated' };
    }

    // Favicon requests
    if (event === 'http_request' && details.url?.includes('/favicon')) {
      return { isNoise: true, reason: 'favicon_request' };
    }

    // Health check endpoints
    if (event === 'http_request' && details.url?.includes('/health')) {
      return { isNoise: true, reason: 'health_check' };
    }

    // Logging system endpoints (prevent infinite loops)
    if (event === 'http_request' && details.url?.includes('/api/logs')) {
      return { isNoise: true, reason: 'logging_endpoint' };
    }

    // Stats endpoints (logging system)
    if (event === 'http_request' && details.url?.includes('/api/logs/stats')) {
      return { isNoise: true, reason: 'logging_stats' };
    }

    // WebSocket connections (system noise)
    if (event === 'http_request' && details.url?.includes('/socket.io')) {
      return { isNoise: true, reason: 'websocket_connection' };
    }

    // Not system noise
    return { isNoise: false };
  }

  /**
   * Check if an API call is a business endpoint worth logging
   */
  private isBusinessAPI(url: string): boolean {
    // Business API endpoints that represent real user actions
    const businessEndpoints = [
      // Customer endpoints
      '/api/customer/',
      '/api/customer/login',
      '/api/customer/register',
      '/api/customer/orders',
      '/api/customer/profile',
      '/api/customer/balance',
      
      // Restaurant endpoints
      '/api/restaurant/',
      '/api/restaurant/login',
      '/api/restaurant/register',
      '/api/restaurant/orders',
      '/api/restaurant/menu',
      '/api/restaurant/profile',
      
      // Restaurant details
      '/api/restaurant_details/',
      '/api/restaurant_details/nearby',
      
      // Order management
      '/api/orders/',
      '/api/orders/create',
      '/api/orders/update',
      '/api/orders/status',
      
      // Menu management
      '/api/menu/',
      '/api/menu/items',
      '/api/menu/categories',
      
      // Payment endpoints
      '/api/payment/',
      '/api/payment/process',
      '/api/payment/status',
      
      // Delivery endpoints
      '/api/delivery/',
      '/api/delivery/status',
      '/api/delivery/track',
      
      // User management
      '/api/user/',
      '/api/user/profile',
      '/api/user/settings',
      
      // Search and discovery
      '/api/search/',
      '/api/search/restaurants',
      '/api/search/menu',
      
      // Reviews and ratings
      '/api/reviews/',
      '/api/reviews/submit',
      '/api/reviews/list'
    ];

    return businessEndpoints.some(endpoint => url.includes(endpoint));
  }

  /**
   * Enhanced system noise detection with business API filtering
   */
  private isSystemNoiseEnhanced(event: string, details: Record<string, any>): { isNoise: boolean; reason?: string } {
    // First check basic system noise
    const basicNoise = this.isSystemNoise(event, details);
    if (basicNoise.isNoise) {
      return basicNoise;
    }

    // For HTTP requests, check if it's a business API (only if strict filtering is enabled)
    if (this.strictBusinessAPIFiltering && event === 'http_request' && details.url) {
      // If it's not a business API, it's likely system noise
      if (!this.isBusinessAPI(details.url)) {
        return { isNoise: true, reason: 'non_business_api' };
      }
    }

    // Not system noise
    return { isNoise: false };
  }

  public enable(): void {
    this.isEnabled = true;
  }

  public disable(): void {
    this.isEnabled = false;
  }

  public clearQueue(): void {
    this.logQueue = [];
  }

  /**
   * Get logs filtered by system noise preference
   */
  public getLogs(includeSystemNoise: boolean = false): UserInteraction[] {
    if (includeSystemNoise) {
      return [...this.logQueue];
    }
    
    // Filter out system noise for user journey view
    return this.logQueue.filter(log => !log.system_noise);
  }

  /**
   * Get only user intent logs (no system noise)
   */
  public getUserJourneyLogs(): UserInteraction[] {
    return this.getLogs(false);
  }

  /**
   * Get system noise logs for debugging
   */
  public getSystemNoiseLogs(): UserInteraction[] {
    return this.logQueue.filter(log => log.system_noise);
  }

  /**
   * Configure system noise handling
   */
  public configureSystemNoise(options: {
    logSystemNoise?: boolean;
    filterSystemNoise?: boolean;
    strictBusinessAPIFiltering?: boolean;
  }): void {
    if (options.logSystemNoise !== undefined) {
      this.logSystemNoise = options.logSystemNoise;
    }
    if (options.filterSystemNoise !== undefined) {
      this.filterSystemNoise = options.filterSystemNoise;
    }
    if (options.strictBusinessAPIFiltering !== undefined) {
      this.strictBusinessAPIFiltering = options.strictBusinessAPIFiltering;
    }
    
    console.log('🔧 System noise configuration updated:', {
      logSystemNoise: this.logSystemNoise,
      filterSystemNoise: this.filterSystemNoise,
      strictBusinessAPIFiltering: this.strictBusinessAPIFiltering
    });
  }

  /**
   * Get current system noise configuration
   */
  public getSystemNoiseConfig(): {
    logSystemNoise: boolean;
    filterSystemNoise: boolean;
    strictBusinessAPIFiltering: boolean;
  } {
    return {
      logSystemNoise: this.logSystemNoise,
      filterSystemNoise: this.filterSystemNoise,
      strictBusinessAPIFiltering: this.strictBusinessAPIFiltering
    };
  }

  private async flushLogs(): Promise<void> {
    if (this.logQueue.length === 0) return;

    const logsToSend = [...this.logQueue];
    this.logQueue = [];
    
    console.log('📤 Flushing logs to backend:', logsToSend.length, 'logs');

    try {
              const response = await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend })
      });

      if (!response.ok) {
        console.error('❌ Failed to send logs to backend:', response.status, response.statusText);
        // Re-add logs to queue if they failed to send
        this.logQueue.unshift(...logsToSend);
      } else {
        console.log('✅ Successfully sent logs to backend');
      }
    } catch (error) {
      console.error('❌ Error sending logs:', error);
      // Re-add logs to queue if they failed to send
      this.logQueue.unshift(...logsToSend);
    }
  }

  private startAutoFlush(): void {
    this.flushTimer = setInterval(() => {
      this.flushLogs();
    }, this.flushInterval);
  }

  public stopAutoFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
  }

  public getCurrentSessionId(): string {
    return this.sessionId;
  }

  public getQueueSize(): number {
    return this.logQueue.length;
  }

  // Manual logging methods for specific interactions
  public logButtonClick(buttonText: string, buttonId?: string, additionalDetails?: Record<string, any>): void {
    this.logInteraction('button_click', {
      trigger: 'click',
      buttonText,
      buttonId,
      schema_version: 'button_click.v1',
      ...additionalDetails
    });
  }

  public logNavigation(from: string, to: string, method: 'link' | 'button' | 'programmatic' = 'link'): void {
    this.logInteraction('navigation', {
      trigger: 'navigation',
      from,
      to,
      method,
      schema_version: 'navigation.v1'
    });
  }

  public logError(error: Error, context?: string): void {
    this.logInteraction('error', {
      trigger: 'error',
      errorMessage: error.message,
      errorStack: error.stack,
      context,
      schema_version: 'error.v1'
    });
  }

  public logPerformance(metric: string, value: number, unit: string = 'ms'): void {
    this.logInteraction('performance', {
      trigger: 'performance',
      metric,
      value,
      unit,
      schema_version: 'performance.v1'
    });
  }
}

// Create singleton instance
export const userLogger = new UserInteractionLogger();

// Export types for use in components
export type { UserInteraction };

// Export the class for testing or advanced usage
export { UserInteractionLogger };

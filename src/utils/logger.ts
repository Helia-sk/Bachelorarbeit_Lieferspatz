interface UserInteraction {
  event: string;
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
  schema: string;
  url: string;
  userAgent: string;
  viewport: {
    width: number;
    height: number;
  };
}

class UserInteractionLogger {
  private sessionId: string;
  private userId?: string;
  private isEnabled: boolean = true;
  private batchSize: number = 10;
  private logQueue: UserInteraction[] = [];
  private flushInterval: number = 5000; // 5 seconds
  private flushTimer?: NodeJS.Timeout;

  constructor() {
    console.log('🚀 UserInteractionLogger initializing...');
    this.sessionId = this.generateSessionId();
    console.log('📝 Session ID:', this.sessionId);
    this.startAutoFlush();
    this.setupGlobalListeners();
    console.log('✅ UserInteractionLogger initialized successfully');
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
              schema: 'click.v1'
            });
          }
        });

    // Capture form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target as HTMLFormElement;
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
        schema: 'form_submit.v1'
      });
    });

    // Capture input changes
    document.addEventListener('input', (e) => {
      const target = e.target as HTMLInputElement;
      if (target && ['input', 'textarea', 'select'].includes(target.tagName.toLowerCase())) {
        this.logInteraction('input_change', {
          trigger: 'input',
          inputName: target.name,
          inputType: target.type,
          inputValue: target.type === 'password' ? '[HIDDEN]' : target.value.substring(0, 100),
          inputId: target.id,
          schema: 'input_change.v1'
        });
      }
    });

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
          schema: 'scroll.v1'
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
          schema: 'window_resize.v1'
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
      schema: 'page_view.v1'
    });
  }

  public logInteraction(event: string, details: Record<string, any> = {}): void {
    if (!this.isEnabled) return;

    const interaction = {
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      event,
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
      schema: details.schema || 'frontend.v1',
      // Additional context
      url: window.location.href,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    };

    console.log('📝 Logging interaction:', { event, details });
    this.logQueue.push(interaction);
    console.log('📊 Queue size:', this.logQueue.length);
    
    // Flush immediately if queue is full
    if (this.logQueue.length >= this.batchSize) {
      console.log('🚀 Flushing logs (queue full)');
      this.flushLogs();
    }
  }

  public setUserId(userId: string): void {
    this.userId = userId;
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
      schema: 'button_click.v1',
      ...additionalDetails
    });
  }

  public logNavigation(from: string, to: string, method: 'link' | 'button' | 'programmatic' = 'link'): void {
    this.logInteraction('navigation', {
      trigger: 'navigation',
      from,
      to,
      method,
      schema: 'navigation.v1'
    });
  }

  public logError(error: Error, context?: string): void {
    this.logInteraction('error', {
      trigger: 'error',
      errorMessage: error.message,
      errorStack: error.stack,
      context,
      schema: 'error.v1'
    });
  }

  public logPerformance(metric: string, value: number, unit: string = 'ms'): void {
    this.logInteraction('performance', {
      trigger: 'performance',
      metric,
      value,
      unit,
      schema: 'performance.v1'
    });
  }
}

// Create singleton instance
export const userLogger = new UserInteractionLogger();

// Export types for use in components
export type { UserInteraction };

// Export the class for testing or advanced usage
export { UserInteractionLogger };

import React, { ReactNode, ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 * Catches rendering errors and displays fallback UI instead of crashing entire app
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Error caught by boundary:', error, errorInfo);
    
    // Send to error tracking service (e.g., Sentry, LogRocket)
    // await logErrorToService(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <section style={{ padding: '40px 20px', textAlign: 'center', minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ maxWidth: '500px', borderLeft: '4px solid #ff6b6b' }}>
            <h2 style={{ color: '#d32f2f', marginBottom: '10px' }}>⚠️ Something Went Wrong</h2>
            <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
              We encountered an unexpected error. Please try refreshing the page or going back.
            </p>
            
            {import.meta.env.DEV && this.state.error && (
              <details style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px', textAlign: 'left' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '10px' }}>
                  Error Details (Dev Only)
                </summary>
                <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '200px', color: '#d32f2f' }}>
                  {this.state.error.toString()}
                  {'\n\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button 
                className="btn btn-primary" 
                onClick={this.handleReset}
                style={{ marginRight: '10px' }}
              >
                Try Again
              </button>
              <button 
                className="btn"
                onClick={() => window.location.href = '/'}
              >
                Go Home
              </button>
            </div>
          </div>
        </section>
      );
    }

    return this.props.children;
  }
}

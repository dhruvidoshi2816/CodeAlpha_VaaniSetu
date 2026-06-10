import { Component } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    });
    // Log to console for debugging
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 px-4">
          <div className="text-center max-w-md">
            <div className="flex justify-center mb-6">
              <div className="p-4 rounded-2xl bg-red-500/20 ring-1 ring-red-500/30">
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
            <p className="text-zinc-400 text-sm mb-6">
              We encountered an unexpected error. Please try again.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-zinc-800 rounded-lg p-4 mb-6 text-left text-xs text-zinc-300 overflow-auto max-h-32">
                <p className="font-mono text-red-400">{this.state.error.toString()}</p>
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-indigo/20 hover:bg-brand-indigo/30 text-brand-cyan font-medium transition-all"
            >
              <RotateCcw className="h-4 w-4" />
              Go Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

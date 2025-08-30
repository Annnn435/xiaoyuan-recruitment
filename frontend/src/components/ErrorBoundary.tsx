import { Component, ReactNode } from 'react';
import { Alert, Card } from 'antd';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error) {
    return {
      hasError: true,
      error,
    };
  }

  render() {
    const { hasError, error } = this.state;
    const { children } = this.props;

    if (hasError) {
      return (
        <Card style={{ marginTop: 16 }}>
          <Alert
            message="发生错误"
            description={error?.message || '未知错误'}
            type="error"
            showIcon
          />
        </Card>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
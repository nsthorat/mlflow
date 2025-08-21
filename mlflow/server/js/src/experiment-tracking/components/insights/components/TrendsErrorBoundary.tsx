/**
 * Error boundary component for trends features
 * Catches and displays errors gracefully with retry functionality
 */

import React, { Component, ReactNode } from 'react';
import { useDesignSystemTheme, Button, Typography, WarningIcon } from '@databricks/design-system';
import { FormattedMessage, useIntl } from 'react-intl';
import { TrendsError } from '../types/insightsTypes';
import { INSIGHTS_ERROR_RETRY_BUTTON_COMPONENT_ID } from '../constants/insightsLogging';

interface TrendsErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: TrendsError, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface TrendsErrorBoundaryState {
  hasError: boolean;
  error: TrendsError | null;
}

/**
 * Error boundary that catches JavaScript errors anywhere in the child component tree
 */
class TrendsErrorBoundaryClass extends Component<TrendsErrorBoundaryProps, TrendsErrorBoundaryState> {
  constructor(props: TrendsErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): TrendsErrorBoundaryState {
    return {
      hasError: true,
      error: {
        message: error.message || 'An unexpected error occurred',
        code: error.name,
        retryable: true,
      },
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('TrendsErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleRetry);
      }

      return <TrendsErrorDisplay error={this.state.error} onRetry={this.handleRetry} />;
    }

    return this.props.children;
  }
}

/**
 * Default error display component
 */
const TrendsErrorDisplay = ({ error, onRetry }: { error: TrendsError; onRetry: () => void }) => {
  const { theme } = useDesignSystemTheme();

  return (
    <div
      css={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: theme.spacing.lg,
        textAlign: 'center',
        gap: theme.spacing.md,
        minHeight: 200,
      }}
    >
      <WarningIcon css={{ fontSize: 48, color: '#ff7b00' }} />
      <div>
        <Typography.Title level={4}>Something went wrong</Typography.Title>
        <Typography.Text color="secondary" css={{ marginTop: theme.spacing.sm }}>
          {error.message}
        </Typography.Text>
        {error.code && (
          <Typography.Text
            color="secondary"
            css={{
              marginTop: theme.spacing.xs,
              fontSize: theme.typography.fontSizeSm,
              fontFamily: 'monospace',
            }}
          >
            Error code: {error.code}
          </Typography.Text>
        )}
      </div>
      {error.retryable && (
        <Button type="primary" onClick={onRetry} componentId={INSIGHTS_ERROR_RETRY_BUTTON_COMPONENT_ID}>
          Try again
        </Button>
      )}
    </div>
  );
};

/**
 * HOC wrapper to make the error boundary easier to use with function components
 */
export const TrendsErrorBoundary = (props: TrendsErrorBoundaryProps) => {
  return <TrendsErrorBoundaryClass {...props} />;
};

/**
 * Hook for handling async errors in components
 */
export const useTrendsErrorHandler = () => {
  const [error, setError] = React.useState<TrendsError | null>(null);

  const handleError = React.useCallback((error: Error | string, retryable = true) => {
    const trendsError: TrendsError = {
      message: typeof error === 'string' ? error : error.message,
      code: typeof error === 'string' ? undefined : error.name,
      retryable,
    };
    setError(trendsError);
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    hasError: error !== null,
    handleError,
    clearError,
  };
};

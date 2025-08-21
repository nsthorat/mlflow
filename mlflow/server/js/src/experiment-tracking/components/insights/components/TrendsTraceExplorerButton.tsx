import React, { useMemo } from 'react';
import { Button } from '@databricks/design-system';

interface TrendsTraceExplorerButtonProps {
  /** Component ID for analytics tracking */
  componentId: string;
  /** Text to display on the button. If not provided, will use "View traces ({count})" or "Explore traces" */
  text?: string;
  /** Number of traces to display in button text. If provided, will show "View traces ({count})" */
  traceCount?: number;
  /** Icon to display next to button text */
  icon?: React.ReactElement;
  /** Button visual style - 'primary', 'tertiary', or 'default' */
  variant?: 'primary' | 'tertiary' | 'default';
  /** Button size */
  size?: 'small';
  /** Whether the button is disabled */
  disabled?: boolean;
  /** Click handler for the button */
  onClick: () => void;
}

/**
 * Shared component for "View traces" and "Explore traces" buttons across different trend pages.
 * Provides consistent styling and behavior for trace exploration functionality.
 *
 * Usage patterns:
 * - Tools page: "Explore traces" with icon, default styling
 * - Traffic/Cost pages: "View traces ({count})" with tertiary styling, no icon
 */
export const TrendsTraceExplorerButton = ({
  componentId,
  text,
  traceCount,
  icon,
  variant = 'default',
  size = 'small',
  disabled = false,
  onClick,
}: TrendsTraceExplorerButtonProps) => {
  // Generate button text based on props
  const buttonText = useMemo(() => {
    if (text) {
      return text;
    }

    if (traceCount !== undefined) {
      return `View traces (${traceCount})`;
    }

    return 'Explore traces';
  }, [text, traceCount]);

  // Determine if button should be disabled
  const isDisabled = disabled || (traceCount !== undefined && traceCount === 0);

  return (
    <Button
      componentId={componentId}
      type={variant === 'default' ? undefined : variant}
      size={size}
      icon={icon}
      disabled={isDisabled}
      onClick={onClick}
    >
      {buttonText}
    </Button>
  );
};

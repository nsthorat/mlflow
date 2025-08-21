/**
 * Card styling constants for trends components
 * Consolidates repeated hardcoded colors, shadows, and other visual elements
 */

export const CARD_STYLES = {
  COLORS: {
    PRIMARY_TEXT: '#11171C',
    BACKGROUND: '#FFFFFF',
    BORDER: '#E8ECF0',
    PROGRESS_BAR: '#077A9D',
  },
  SHADOWS: {
    DEFAULT: '0px 2px 3px -1px rgba(0, 0, 0, 0.05), 0px 1px 0px 0px rgba(0, 0, 0, 0.02)',
    HOVER: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px 0px rgba(0, 0, 0, 0.06)',
  },
  BORDERS: {
    DEFAULT: '1px solid #E8ECF0',
  },
} as const;

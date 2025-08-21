/**
 * Unit tests for time transformation utilities
 */

import {
  msToSeconds,
  formatLatency,
  formatPercentage,
  formatCount,
  calculatePercentage,
} from './timeTransformationUtils';

describe('msToSeconds', () => {
  it('should convert milliseconds to seconds', () => {
    expect(msToSeconds(1000)).toBe(1);
    expect(msToSeconds(5500)).toBe(5.5);
    expect(msToSeconds(0)).toBe(0);
  });
});

describe('formatLatency', () => {
  it('should format latency with 2 decimal places for values >= 1000ms, otherwise as ms', () => {
    expect(formatLatency(1000)).toBe('1.00s');
    expect(formatLatency(1500)).toBe('1.50s');
    expect(formatLatency(123)).toBe('123ms');
  });
});

describe('formatPercentage', () => {
  it('should format decimal to percentage', () => {
    expect(formatPercentage(0.1)).toBe('10.0%');
    expect(formatPercentage(0.567)).toBe('56.7%');
    expect(formatPercentage(0.1, 2)).toBe('10.00%');
  });
});

describe('formatCount', () => {
  it('should format count with locale string', () => {
    expect(formatCount(1000)).toBe('1,000');
    expect(formatCount(123456)).toBe('123,456');
    expect(formatCount(42)).toBe('42');
  });
});

describe('calculatePercentage', () => {
  it('should calculate percentage from count and total', () => {
    expect(calculatePercentage(25, 100)).toBe(25);
    expect(calculatePercentage(1, 3)).toBeCloseTo(33.33, 2);
    expect(calculatePercentage(0, 100)).toBe(0);
    expect(calculatePercentage(5, 0)).toBe(0);
  });
});

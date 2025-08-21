/**
 * Unit tests for legacy data transformation utilities
 * @deprecated - Use individual utility files instead
 */

import { msToSeconds, formatLatency, formatPercentage } from './timeTransformationUtils';
import {
  safeNumberConversion,
  getNPMIStrength,
  transformLatencyPercentiles,
  transformErrorRateData,
} from './dataProcessingUtils';

describe('TIME_TRANSFORMATIONS (legacy)', () => {
  describe('msToSeconds', () => {
    it('should convert milliseconds to seconds', () => {
      expect(msToSeconds(1000)).toBe(1);
      expect(msToSeconds(5500)).toBe(5.5);
      expect(msToSeconds(0)).toBe(0);
    });
  });

  describe('formatLatency', () => {
    it('should format latency as ms for values < 1000, and as seconds for values >= 1000', () => {
      expect(formatLatency(50)).toBe('50ms');
      expect(formatLatency(999)).toBe('999ms');
      expect(formatLatency(1000)).toBe('1.00s');
      expect(formatLatency(1500)).toBe('1.50s');
      expect(formatLatency(2345)).toBe('2.35s');
    });
  });

  describe('formatPercentage', () => {
    it('should format decimal to percentage', () => {
      expect(formatPercentage(0.1)).toBe('10.0%');
      expect(formatPercentage(0.567)).toBe('56.7%');
      expect(formatPercentage(0.1, 2)).toBe('10.00%');
    });
  });
});

describe('DATA_PROCESSING (legacy)', () => {
  describe('safeNumberConversion', () => {
    it('should safely convert values to numbers', () => {
      expect(safeNumberConversion('123')).toBe(123);
      expect(safeNumberConversion(456)).toBe(456);
      expect(safeNumberConversion(undefined)).toBe(0);
      expect(safeNumberConversion('invalid')).toBe(0);
      expect(safeNumberConversion('invalid', 99)).toBe(99);
    });
  });

  describe('getNPMIStrength', () => {
    it('should categorize NPMI values correctly', () => {
      expect(getNPMIStrength(0.8)).toBe('strong'); // >= 0.7
      expect(getNPMIStrength(0.5)).toBe('moderate'); // >= 0.3, < 0.7
      expect(getNPMIStrength(0.2)).toBe('weak'); // >= 0.1, < 0.3
      expect(getNPMIStrength(0.05)).toBe('none'); // > 0, < 0.1
      expect(getNPMIStrength(0)).toBe('negative'); // = 0 falls through to negative
      expect(getNPMIStrength(-0.2)).toBe('negative'); // < 0
    });
  });

  describe('transformLatencyPercentiles', () => {
    it('should transform latency data for charts', () => {
      const input = [{ timeBucket: '2025-01-10T10:00:00Z', p50: 1000, p90: 2000, p99: 3000 }];

      const result = transformLatencyPercentiles(input);

      expect(result).toHaveLength(3);
      expect(result[0]).toMatchObject({
        timeBucket: new Date('2025-01-10T10:00:00Z'),
        value: 1000, // Keep in milliseconds
        seriesName: 'P50',
      });
      expect(result[1].seriesName).toBe('P90');
      expect(result[2].seriesName).toBe('P99');
    });
  });

  describe('transformErrorRateData', () => {
    it('should transform error rate data', () => {
      const input = [{ timeBucket: '2025-01-10T10:00:00Z', value: 0.1 }];

      const result = transformErrorRateData(input);

      expect(result).toHaveLength(1);
      expect(result[0]).toMatchObject({
        timeBucket: new Date('2025-01-10T10:00:00Z'),
        value: 0.1,
      });
    });
  });
});

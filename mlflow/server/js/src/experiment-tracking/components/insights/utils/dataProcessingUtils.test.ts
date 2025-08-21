/**
 * Unit tests for data processing utilities
 */

import {
  transformTimeBucketData,
  safeNumberConversion,
  getNPMIStrength,
  transformLatencyPercentiles,
  transformErrorRateData,
} from './dataProcessingUtils';

describe('transformTimeBucketData', () => {
  it('should transform time bucket data', () => {
    const input = [
      { timeBucket: '2025-01-10T10:00:00Z', value: 100 },
      { timeBucket: new Date('2025-01-10T11:00:00Z'), value: 200 },
    ];

    const result = transformTimeBucketData(input);

    expect(result).toHaveLength(2);
    expect(result[0].timeBucket).toBeInstanceOf(Date);
    expect(result[0].value).toBe(100);
    expect(result[1].timeBucket).toBeInstanceOf(Date);
    expect(result[1].value).toBe(200);
  });
});

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

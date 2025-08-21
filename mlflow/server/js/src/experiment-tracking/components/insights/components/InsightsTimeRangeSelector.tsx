import React, { useMemo } from 'react';
import {
  Button,
  DialogCombobox,
  DialogComboboxContent,
  DialogComboboxOptionList,
  DialogComboboxOptionListSelectItem,
  DialogComboboxTrigger,
  RefreshIcon,
  Tooltip,
  useDesignSystemTheme,
} from '@databricks/design-system';
import { FormattedMessage, useIntl } from 'react-intl';
import { useInsightsTimeRange, DEFAULT_INSIGHTS_TIME_RANGE, type InsightsTimeRange } from '../hooks/useInsightsTimeRange';

const getInsightsTimeRangeLabels = (intl: any) => ({
  LAST_HOUR: intl.formatMessage({
    defaultMessage: 'Last hour',
    description: 'Option for the time range dropdown to show data from the last hour',
  }),
  LAST_24_HOURS: intl.formatMessage({
    defaultMessage: 'Last 24 hours',
    description: 'Option for the time range dropdown to show data from the last 24 hours',
  }),
  LAST_7_DAYS: intl.formatMessage({
    defaultMessage: 'Last 7 days',
    description: 'Option for the time range dropdown to show data from the last 7 days',
  }),
  LAST_30_DAYS: intl.formatMessage({
    defaultMessage: 'Last 30 days',
    description: 'Option for the time range dropdown to show data from the last 30 days',
  }),
  LAST_YEAR: intl.formatMessage({
    defaultMessage: 'Last year',
    description: 'Option for the time range dropdown to show data from the last year',
  }),
  ALL: intl.formatMessage({
    defaultMessage: 'All time',
    description: 'Option for the time range dropdown to show all data',
  }),
});

export const InsightsTimeRangeSelector = React.memo(() => {
  const intl = useIntl();
  const { theme } = useDesignSystemTheme();

  const [timeRangeFilters, setTimeRangeFilters, refreshDateNow] = useInsightsTimeRange();

  const timeRangeLabels = useMemo(() => getInsightsTimeRangeLabels(intl), [intl]);

  // List of available time ranges (excluding CUSTOM for now)
  const availableTimeRanges: InsightsTimeRange[] = [
    'LAST_HOUR',
    'LAST_24_HOURS', 
    'LAST_7_DAYS',
    'LAST_30_DAYS',
    'LAST_YEAR',
    'ALL',
  ];

  const currentTimeRangeLabel = intl.formatMessage({
    defaultMessage: 'Time Range',
    description: 'Label for the time range select dropdown for insights view',
  });

  const currentTimeRange = timeRangeFilters.timeRange || DEFAULT_INSIGHTS_TIME_RANGE;

  return (
    <div
      css={{
        display: 'flex',
        gap: theme.spacing.sm,
        alignItems: 'center',
      }}
    >
      <DialogCombobox
        componentId="insights-time-range-selector"
        label={currentTimeRangeLabel}
        value={[timeRangeLabels[currentTimeRange] || timeRangeLabels[DEFAULT_INSIGHTS_TIME_RANGE]]}
      >
        <DialogComboboxTrigger
          allowClear={false}
          data-testid="insights-time-range-select-dropdown"
        />
        <DialogComboboxContent>
          <DialogComboboxOptionList>
            {availableTimeRanges.map((timeRange) => (
              <DialogComboboxOptionListSelectItem
                key={timeRange}
                checked={currentTimeRange === timeRange}
                title={timeRangeLabels[timeRange]}
                data-testid={`insights-time-range-select-${timeRange}`}
                value={timeRange}
                onChange={() => {
                  setTimeRangeFilters({
                    ...timeRangeFilters,
                    timeRange,
                  });
                }}
              >
                {timeRangeLabels[timeRange]}
              </DialogComboboxOptionListSelectItem>
            ))}
          </DialogComboboxOptionList>
        </DialogComboboxContent>
      </DialogCombobox>
      <Tooltip
        componentId="insights-time-range-refresh-tooltip"
        content={intl.formatMessage(
          {
            defaultMessage: 'Showing data up to {date}. Click to refresh with current time.',
            description: 'Tooltip for the refresh button showing the pinned date and time',
          },
          {
            date: timeRangeFilters.dateNow?.toLocaleString(navigator.language, {
              timeZoneName: 'short',
            }) || 'now',
          },
        )}
      >
        <Button
          type="link"
          componentId="insights-time-range-refresh-button"
          onClick={refreshDateNow}
        >
          <RefreshIcon />
        </Button>
      </Tooltip>
    </div>
  );
});
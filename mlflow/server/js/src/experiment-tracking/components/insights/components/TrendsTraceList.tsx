import React, { useMemo, useCallback } from 'react';
import { getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table';
import { useDesignSystemTheme, Table, TableRow, TableHeader, TableCell, Tag, Tooltip } from '@databricks/design-system';
import { TraceEntry, TraceListColumn } from '../types/insightsTypes';
import Utils from '@mlflow/mlflow/src/common/utils/Utils';
import { TrendsTraceListSkeleton } from './TrendsSkeleton';
import {
  TRENDS_TRACE_LIST_STATUS_COMPONENT_ID,
  TRENDS_TRACE_REQUEST_TOOLTIP_COMPONENT_ID,
  TRENDS_TRACE_LIST_HEADER_COMPONENT_ID,
} from '../constants/insightsLogging';

interface TrendsTraceListProps {
  traces: TraceEntry[];
  selectedTraceId: string | null;
  onTraceSelect: (traceId: string) => void;
  visibleColumns?: TraceListColumn[];
  isLoading?: boolean;
}

export const TrendsTraceList = ({
  traces,
  selectedTraceId,
  onTraceSelect,
  visibleColumns = ['execution_duration', 'state', 'request_time'],
  isLoading = false,
}: TrendsTraceListProps) => {
  const { theme } = useDesignSystemTheme();

  const getStatusTag = useCallback(
    (state: string) => {
      const color = state.toLowerCase() === 'error' ? 'coral' : state.toLowerCase() === 'ok' ? 'lime' : 'lemon';

      return (
        <Tag
          componentId={TRENDS_TRACE_LIST_STATUS_COMPONENT_ID}
          color={color}
          css={{ fontSize: theme.typography.fontSizeSm }}
        >
          {state}
        </Tag>
      );
    },
    [theme.typography.fontSizeSm],
  );

  const columns = useMemo<ColumnDef<TraceEntry>[]>(() => {
    const baseColumns: ColumnDef<TraceEntry>[] = [
      {
        id: 'request',
        header: 'Request',
        accessorFn: (row: TraceEntry) => row['request'],
        size: 400,
        minSize: 200,
        maxSize: 600,
        // eslint-disable-next-line @databricks/no-unstable-nested-components
        cell: ({ getValue }) => {
          const rawRequest = getValue() as string;

          // Quick test - try to extract content directly
          let displayText = rawRequest;
          try {
            const parsed = JSON.parse(rawRequest);
            if (parsed.messages && parsed.messages[0] && parsed.messages[0].content) {
              displayText = parsed.messages[0].content;
            }
          } catch {
            // Keep original if parsing fails
            // eslint-disable-next-line no-console
            console.error('Failed to parse request:', rawRequest);
          }

          return (
            <div
              css={{
                fontSize: theme.typography.fontSizeSm,
                color: theme.colors.textPrimary,
                lineHeight: '1.4',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
              }}
            >
              <Tooltip
                componentId={TRENDS_TRACE_REQUEST_TOOLTIP_COMPONENT_ID}
                content={
                  <div css={{ maxWidth: 400, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{displayText}</div>
                }
              >
                <div>{displayText}</div>
              </Tooltip>
            </div>
          );
        },
      },
    ];

    if (visibleColumns.includes('execution_duration')) {
      baseColumns.push({
        id: 'execution_duration',
        header: 'Duration',
        accessorFn: (row: TraceEntry) => row['execution_duration'],
        size: 80,
        minSize: 60,
        maxSize: 120,
        // eslint-disable-next-line @databricks/no-unstable-nested-components
        cell: ({ getValue }) => {
          const duration = getValue() as string | undefined;
          const durationMs = duration ? Number(duration) : 0;
          return (
            <div
              css={{
                fontSize: theme.typography.fontSizeSm,
                color: theme.colors.textSecondary,
                textAlign: 'right' as const,
              }}
            >
              {Utils.formatDuration(durationMs)}
            </div>
          );
        },
      });
    }

    if (visibleColumns.includes('state')) {
      baseColumns.push({
        id: 'state',
        header: 'Status',
        accessorFn: (row: TraceEntry) => row['state'],
        size: 90,
        minSize: 75,
        maxSize: 120,
        // eslint-disable-next-line @databricks/no-unstable-nested-components
        cell: ({ getValue }) => {
          const state = getValue() as string;
          return getStatusTag(state);
        },
      });
    }

    if (visibleColumns.includes('request_time')) {
      baseColumns.push({
        id: 'request_time',
        header: 'Time',
        accessorFn: (row: TraceEntry) => row['request_time'],
        size: 120,
        minSize: 100,
        maxSize: 150,
        // eslint-disable-next-line @databricks/no-unstable-nested-components
        cell: ({ getValue }) => {
          const requestTime = getValue() as string;
          return (
            <div
              css={{
                fontSize: theme.typography.fontSizeSm,
                color: theme.colors.textSecondary,
              }}
            >
              {new Date(requestTime).toLocaleTimeString()}
            </div>
          );
        },
      });
    }

    return baseColumns;
  }, [visibleColumns, theme, getStatusTag]);

  const table = useReactTable({
    data: traces,
    columns,
    getCoreRowModel: getCoreRowModel(),
    enableColumnResizing: false,
  });

  const columnSizeVars = useMemo(() => {
    const headers = table.getHeaderGroups().flatMap((group) => group.headers);
    const vars: Record<string, string> = {};
    headers.forEach((header) => {
      const escapedId = CSS.escape(header.id);
      vars[`--header-${escapedId}-size`] = `${header.getSize()}px`;
      vars[`--col-${escapedId}-size`] = `${header.column.getSize()}px`;
    });
    return vars;
  }, [table]);

  if (isLoading) {
    return <TrendsTraceListSkeleton />;
  }

  return (
    <div css={{ padding: theme.spacing.sm }}>
      <div
        css={{
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        <Table
          css={{
            width: '100%',
            tableLayout: 'fixed',
            ...columnSizeVars,
          }}
        >
          <TableRow isHeader>
            {table.getHeaderGroups().map((headerGroup) =>
              headerGroup.headers.map((header) => {
                const escapedId = CSS.escape(header.id);
                return (
                  <TableHeader
                    key={header.id}
                    componentId={`${TRENDS_TRACE_LIST_HEADER_COMPONENT_ID}-${header.id}`}
                    style={{
                      width: `var(--header-${escapedId}-size)`,
                      flex: 'revert',
                      ...(header.column.id === 'request' && { flexGrow: 1 }),
                    }}
                    css={{
                      padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
                    }}
                  >
                    {header.isPlaceholder ? null : (header.column.columnDef.header as string)}
                  </TableHeader>
                );
              }),
            )}
          </TableRow>
          {table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.original.trace_id}
              onClick={() => onTraceSelect(row.original.trace_id || '')}
              css={{
                cursor: 'pointer',
                backgroundColor:
                  row.original.trace_id === selectedTraceId ? theme.colors.actionDefaultBackgroundPress : 'transparent',
                borderLeft:
                  row.original.trace_id === selectedTraceId
                    ? `3px solid ${theme.colors.actionDefaultBorderPress}`
                    : '3px solid transparent',
                '&:hover': {
                  backgroundColor: theme.colors.actionDefaultBackgroundHover,
                },
              }}
            >
              {row.getVisibleCells().map((cell) => {
                const escapedId = CSS.escape(cell.column.id);
                return (
                  <TableCell
                    key={cell.id}
                    style={{
                      width: `var(--col-${escapedId}-size)`,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 'revert',
                      ...(cell.column.id === 'request' && {
                        flexGrow: 1,
                        whiteSpace: 'normal',
                        wordBreak: 'break-word',
                      }),
                    }}
                    css={{
                      padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
                    }}
                  >
                    {cell.renderValue()}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </Table>
      </div>
    </div>
  );
};

import { useSearchParams } from '../../../../common/utils/RoutingUtils';

export type InsightsPageMode = 'traffic' | 'quality' | 'tools' | 'tags' | 'topics' | 'create';

export const INSIGHTS_SUBPAGE_QUERY_PARAM_KEY = 'insightsSubpage';

export const getInsightsPageDefaultMode = (): InsightsPageMode => 'traffic';

/**
 * Hook using search params to retrieve and update the current insights subpage mode.
 * Uses the "insightsSubpage" query parameter to track which insights page is active.
 * @param initialMode - Optional initial mode to use if no query param is present
 */
export const useInsightsPageMode = (initialMode?: InsightsPageMode): [
  InsightsPageMode,
  (newMode: InsightsPageMode) => void,
] => {
  const [params, setParams] = useSearchParams();

  const mode =
    (params.get(INSIGHTS_SUBPAGE_QUERY_PARAM_KEY) as InsightsPageMode) ||
    initialMode ||
    getInsightsPageDefaultMode();

  const setMode = (newMode: InsightsPageMode) => {
    setParams(
      (currentParams) => {
        if (newMode === getInsightsPageDefaultMode()) {
          // If setting to default, remove the param to keep URL clean
          currentParams.delete(INSIGHTS_SUBPAGE_QUERY_PARAM_KEY);
        } else {
          currentParams.set(INSIGHTS_SUBPAGE_QUERY_PARAM_KEY, newMode);
        }
        return currentParams;
      },
      { replace: true }, // Use replace to avoid polluting browser history with subpage changes
    );
  };

  return [mode, setMode];
};
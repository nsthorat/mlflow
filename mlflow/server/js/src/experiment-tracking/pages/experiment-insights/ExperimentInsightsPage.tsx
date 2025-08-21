import { useEffect, useMemo } from 'react';
import invariant from 'invariant';
import { useNavigate, useParams } from '../../../common/utils/RoutingUtils';
import { InsightsView } from '../../components/insights/InsightsView';
import { shouldEnableExperimentPageHeaderV2 } from '../../../common/utils/FeatureUtils';
import Routes from '../../routes';

const ExperimentInsightsPage = () => {
  const { experimentId } = useParams();
  invariant(experimentId, 'Experiment ID must be defined');

  const navigate = useNavigate();
  useEffect(() => {
    if (experimentId && !shouldEnableExperimentPageHeaderV2()) {
      navigate(Routes.getExperimentPageRoute(experimentId));
    }
  }, [experimentId, navigate]);

  return <InsightsView experimentId={experimentId} />;
};

export default ExperimentInsightsPage;
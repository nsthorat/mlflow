import base64
import json
import re

import pytest

from mlflow.entities import (
    Dataset,
    DatasetInput,
    InputTag,
    LifecycleStage,
    Metric,
    Param,
    Run,
    RunData,
    RunInfo,
    RunInputs,
    RunStatus,
    RunTag,
)
from mlflow.exceptions import MlflowException
from mlflow.utils.mlflow_tags import MLFLOW_DATASET_CONTEXT
from mlflow.utils.search_utils import SearchUtils


@pytest.mark.parametrize(
    ("filter_string", "parsed_filter"),
    [
        (
            "metric.acc >= 0.94",
            [{"comparator": ">=", "key": "acc", "type": "metric", "value": "0.94"}],
        ),
        ("metric.acc>=100", [{"comparator": ">=", "key": "acc", "type": "metric", "value": "100"}]),
        ("params.m!='tf'", [{"comparator": "!=", "key": "m", "type": "parameter", "value": "tf"}]),
        (
            'params."m"!="tf"',
            [{"comparator": "!=", "key": "m", "type": "parameter", "value": "tf"}],
        ),
        (
            'metric."legit name" >= 0.243',
            [{"comparator": ">=", "key": "legit name", "type": "metric", "value": "0.243"}],
        ),
        ("metrics.XYZ = 3", [{"comparator": "=", "key": "XYZ", "type": "metric", "value": "3"}]),
        (
            'params."cat dog" = "pets"',
            [{"comparator": "=", "key": "cat dog", "type": "parameter", "value": "pets"}],
        ),
        (
            'metrics."X-Y-Z" = 3',
            [{"comparator": "=", "key": "X-Y-Z", "type": "metric", "value": "3"}],
        ),
        (
            'metrics."X//Y#$$@&Z" = 3',
            [{"comparator": "=", "key": "X//Y#$$@&Z", "type": "metric", "value": "3"}],
        ),
        (
            "params.model = 'LinearRegression'",
            [{"comparator": "=", "key": "model", "type": "parameter", "value": "LinearRegression"}],
        ),
        (
            "metrics.rmse < 1 and params.model_class = 'LR'",
            [
                {"comparator": "<", "key": "rmse", "type": "metric", "value": "1"},
                {"comparator": "=", "key": "model_class", "type": "parameter", "value": "LR"},
            ],
        ),
        ("", []),
        ("`metric`.a >= 0.1", [{"comparator": ">=", "key": "a", "type": "metric", "value": "0.1"}]),
        (
            "`params`.model >= 'LR'",
            [{"comparator": ">=", "key": "model", "type": "parameter", "value": "LR"}],
        ),
        (
            "tags.version = 'commit-hash'",
            [{"comparator": "=", "key": "version", "type": "tag", "value": "commit-hash"}],
        ),
        (
            "`tags`.source_name = 'a notebook'",
            [{"comparator": "=", "key": "source_name", "type": "tag", "value": "a notebook"}],
        ),
        (
            'metrics."accuracy.2.0" > 5',
            [{"comparator": ">", "key": "accuracy.2.0", "type": "metric", "value": "5"}],
        ),
        (
            "metrics.`spacey name` > 5",
            [{"comparator": ">", "key": "spacey name", "type": "metric", "value": "5"}],
        ),
        (
            'params."p.a.r.a.m" != "a"',
            [{"comparator": "!=", "key": "p.a.r.a.m", "type": "parameter", "value": "a"}],
        ),
        ('tags."t.a.g" = "a"', [{"comparator": "=", "key": "t.a.g", "type": "tag", "value": "a"}]),
        (
            "attribute.artifact_uri = '1/23/4'",
            [{"type": "attribute", "comparator": "=", "key": "artifact_uri", "value": "1/23/4"}],
        ),
        (
            "attribute.start_time >= 1234",
            [{"type": "attribute", "comparator": ">=", "key": "start_time", "value": "1234"}],
        ),
        (
            "run.status = 'RUNNING'",
            [{"type": "attribute", "comparator": "=", "key": "status", "value": "RUNNING"}],
        ),
        (
            "dataset.name = 'my_dataset'",
            [{"type": "dataset", "comparator": "=", "key": "name", "value": "my_dataset"}],
        ),
    ],
)
def test_filter(filter_string, parsed_filter):
    assert SearchUtils.parse_search_filter(filter_string) == parsed_filter


@pytest.mark.parametrize(
    ("filter_string", "parsed_filter"),
    [
        ("params.m = 'LR'", [{"type": "parameter", "comparator": "=", "key": "m", "value": "LR"}]),
        ('params.m = "LR"', [{"type": "parameter", "comparator": "=", "key": "m", "value": "LR"}]),
        (
            'params.m = "L\'Hosp"',
            [{"type": "parameter", "comparator": "=", "key": "m", "value": "L'Hosp"}],
        ),
    ],
)
def test_correct_quote_trimming(filter_string, parsed_filter):
    assert SearchUtils.parse_search_filter(filter_string) == parsed_filter


@pytest.mark.parametrize(
    ("filter_string", "error_message"),
    [
        ("metric.acc >= 0.94; metrics.rmse < 1", "Search filter contained multiple expression"),
        ("m.acc >= 0.94", "Invalid entity type"),
        ("acc >= 0.94", "Invalid attribute key"),
        ("p.model >= 'LR'", "Invalid entity type"),
        ("attri.x != 1", "Invalid entity type"),
        ("a.x != 1", "Invalid entity type"),
        ("model >= 'LR'", "Invalid attribute key"),
        ("metrics.A > 0.1 OR params.B = 'LR'", "Invalid clause(s) in filter string"),
        ("metrics.A > 0.1 NAND params.B = 'LR'", "Invalid clause(s) in filter string"),
        ("metrics.A > 0.1 AND (params.B = 'LR')", "Invalid clause(s) in filter string"),
        ("`metrics.A > 0.1", "Invalid clause(s) in filter string"),
        ("param`.A > 0.1", "Invalid clause(s) in filter string"),
        ("`dummy.A > 0.1", "Invalid clause(s) in filter string"),
        ("dummy`.A > 0.1", "Invalid clause(s) in filter string"),
        ("attribute.start != 1", "Invalid attribute key"),
        ("attribute.experiment_id != 1", "Invalid attribute key"),
        ("attribute.lifecycle_stage = 'ACTIVE'", "Invalid attribute key"),
        ("attribute.name != 1", "Invalid attribute key"),
        ("attribute.time != 1", "Invalid attribute key"),
        ("attribute._status != 'RUNNING'", "Invalid attribute key"),
        ("attribute.status = true", "Invalid clause(s) in filter string"),
        ("dataset.status = 'true'", "Invalid dataset key"),
        ("dataset.profile = 'num_rows: 10'", "Invalid dataset key"),
    ],
)
def test_error_filter(filter_string, error_message):
    with pytest.raises(MlflowException, match=re.escape(error_message)):
        SearchUtils.parse_search_filter(filter_string)


@pytest.mark.parametrize(
    ("filter_string", "error_message"),
    [
        ("metric.model = 'LR'", "Expected numeric value type for metric"),
        ("metric.model = '5'", "Expected numeric value type for metric"),
        ("params.acc = 5", "Expected a quoted string value for param"),
        ("tags.acc = 5", "Expected a quoted string value for tag"),
        ("metrics.acc != metrics.acc", "Expected numeric value type for metric"),
        ("1.0 > metrics.acc", "Expected 'Identifier' found"),
        ("attribute.status = 1", "Expected a quoted string value for attributes"),
    ],
)
def test_error_comparison_clauses(filter_string, error_message):
    with pytest.raises(MlflowException, match=error_message):
        SearchUtils.parse_search_filter(filter_string)


@pytest.mark.parametrize(
    ("filter_string", "error_message"),
    [
        ("params.acc = LR", "value is either not quoted or unidentified quote types"),
        ("tags.acc = LR", "value is either not quoted or unidentified quote types"),
        ("params.acc = `LR`", "value is either not quoted or unidentified quote types"),
        ("params.'acc = LR", "Invalid clause(s) in filter string"),
        ("params.acc = 'LR", "Invalid clause(s) in filter string"),
        ("params.acc = LR'", "Invalid clause(s) in filter string"),
        ("params.acc = \"LR'", "Invalid clause(s) in filter string"),
        ("tags.acc = \"LR'", "Invalid clause(s) in filter string"),
        ("tags.acc = = 'LR'", "Invalid clause(s) in filter string"),
        ("attribute.status IS 'RUNNING'", "Invalid clause(s) in filter string"),
    ],
)
def test_bad_quotes(filter_string, error_message):
    with pytest.raises(MlflowException, match=re.escape(error_message)):
        SearchUtils.parse_search_filter(filter_string)


@pytest.mark.parametrize(
    ("filter_string", "error_message"),
    [
        ("params.acc LR !=", "Invalid clause(s) in filter string"),
        ("params.acc LR", "Invalid clause(s) in filter string"),
        ("metric.acc !=", "Invalid clause(s) in filter string"),
        ("acc != 1.0", "Invalid attribute key"),
        ("foo is null", "Invalid clause(s) in filter string"),
        ("1=1", "Expected 'Identifier' found"),
        ("1==2", "Expected 'Identifier' found"),
    ],
)
def test_invalid_clauses(filter_string, error_message):
    with pytest.raises(MlflowException, match=re.escape(error_message)):
        SearchUtils.parse_search_filter(filter_string)


@pytest.mark.parametrize(
    ("entity_type", "bad_comparators", "key", "entity_value"),
    [
        ("metrics", ["~", "~="], "abc", 1.0),
        ("params", [">", "<", ">=", "<=", "~"], "abc", "'my-param-value'"),
        ("tags", [">", "<", ">=", "<=", "~"], "abc", "'my-tag-value'"),
        ("attributes", [">", "<", ">=", "<=", "~"], "status", "'my-tag-value'"),
        ("attributes", ["LIKE", "ILIKE"], "start_time", 1234),
        ("datasets", [">", "<", ">=", "<=", "~"], "name", "'my-dataset-name'"),
    ],
)
def test_bad_comparators(entity_type, bad_comparators, key, entity_value):
    run = Run(
        run_info=RunInfo(
            run_id="hi",
            experiment_id=0,
            user_id="user-id",
            status=RunStatus.to_string(RunStatus.FAILED),
            start_time=0,
            end_time=1,
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        run_data=RunData(metrics=[], params=[], tags=[]),
    )
    for bad_comparator in bad_comparators:
        bad_filter = f"{entity_type}.{key} {bad_comparator} {entity_value}"
        with pytest.raises(MlflowException, match="Invalid comparator"):
            SearchUtils.filter([run], bad_filter)


@pytest.mark.parametrize(
    ("filter_string", "matching_runs"),
    [
        (None, [0, 1, 2]),
        ("", [0, 1, 2]),
        ("attributes.status = 'FAILED'", [0, 2]),
        ("metrics.key1 = 123", [1]),
        ("metrics.key1 != 123", [0, 2]),
        ("metrics.key1 >= 123", [1, 2]),
        ("params.my_param = 'A'", [0, 1]),
        ("tags.tag1 = 'D'", [2]),
        ("tags.tag1 != 'D'", [1]),
        ("params.my_param = 'A' AND attributes.status = 'FAILED'", [0]),
        ("datasets.name = 'name1'", [0, 1]),
        ("datasets.name IN ('name1', 'name2')", [0, 1, 2]),
        ("datasets.digest IN ('digest1', 'digest2')", [0, 1, 2]),
        ("datasets.name = 'name1' AND datasets.digest = 'digest2'", []),
        ("datasets.context = 'train'", [0]),
        ("datasets.name = 'name1' AND datasets.context = 'train'", [0]),
    ],
)
def test_correct_filtering(filter_string, matching_runs):
    runs = [
        Run(
            run_info=RunInfo(
                run_id="hi",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 121, 1, 0)], params=[Param("my_param", "A")], tags=[]
            ),
            run_inputs=RunInputs(
                dataset_inputs=[
                    DatasetInput(
                        dataset=Dataset(
                            name="name1",
                            digest="digest1",
                            source_type="my_source_type",
                            source="source",
                        ),
                        tags=[InputTag(MLFLOW_DATASET_CONTEXT, "train")],
                    )
                ]
            ),
        ),
        Run(
            run_info=RunInfo(
                run_id="hi2",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 123, 1, 0)],
                params=[Param("my_param", "A")],
                tags=[RunTag("tag1", "C")],
            ),
            run_inputs=RunInputs(
                dataset_inputs=[
                    DatasetInput(
                        dataset=Dataset(
                            name="name1",
                            digest="digest1",
                            source_type="my_source_type",
                            source="source",
                        ),
                        tags=[],
                    )
                ]
            ),
        ),
        Run(
            run_info=RunInfo(
                run_id="hi3",
                experiment_id=1,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 125, 1, 0)],
                params=[Param("my_param", "B")],
                tags=[RunTag("tag1", "D")],
            ),
            run_inputs=RunInputs(
                dataset_inputs=[
                    DatasetInput(
                        dataset=Dataset(
                            name="name2",
                            digest="digest2",
                            source_type="my_source_type",
                            source="source",
                        ),
                        tags=[],
                    )
                ]
            ),
        ),
    ]
    filtered_runs = SearchUtils.filter(runs, filter_string)
    assert set(filtered_runs) == {runs[i] for i in matching_runs}


def test_filter_runs_by_start_time():
    runs = [
        Run(
            run_info=RunInfo(
                run_id=run_id,
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=idx,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(),
        )
        for idx, run_id in enumerate(["a", "b", "c"])
    ]
    assert SearchUtils.filter(runs, "attribute.start_time >= 0") == runs
    assert SearchUtils.filter(runs, "attribute.start_time > 1") == runs[2:]
    assert SearchUtils.filter(runs, "attribute.start_time = 2") == runs[2:]


def test_filter_runs_by_user_id():
    runs = [
        Run(
            run_info=RunInfo(
                run_id="a",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=1,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(),
        ),
        Run(
            run_info=RunInfo(
                run_id="b",
                experiment_id=0,
                user_id="user-id2",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=1,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(),
        ),
    ]
    assert SearchUtils.filter(runs, "attribute.user_id = 'user-id2'")[0] == runs[1]


def test_filter_runs_by_end_time():
    runs = [
        Run(
            run_info=RunInfo(
                run_id=run_id,
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=idx,
                end_time=idx,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(),
        )
        for idx, run_id in enumerate(["a", "b", "c"])
    ]
    assert SearchUtils.filter(runs, "attribute.end_time >= 0") == runs
    assert SearchUtils.filter(runs, "attribute.end_time > 1") == runs[2:]
    assert SearchUtils.filter(runs, "attribute.end_time = 2") == runs[2:]


@pytest.mark.parametrize(
    ("order_bys", "matching_runs"),
    [
        (None, [2, 1, 0]),
        ([], [2, 1, 0]),
        (["tags.noSuchTag"], [2, 1, 0]),
        (["attributes.status"], [2, 0, 1]),
        (["attributes.start_time"], [0, 2, 1]),
        (["metrics.key1 asc"], [0, 1, 2]),
        (['metrics."key1"  desc'], [2, 1, 0]),
        (["params.my_param"], [1, 0, 2]),
        (["params.my_param aSc", "attributes.status  ASC"], [0, 1, 2]),
        (["params.my_param", "attributes.status DESC"], [1, 0, 2]),
        (["params.my_param DESC", "attributes.status   DESC"], [2, 1, 0]),
        (["params.`my_param` DESC", "attributes.status DESC"], [2, 1, 0]),
        (["tags.tag1"], [1, 2, 0]),
        (["tags.tag1    DESC"], [2, 1, 0]),
    ],
)
def test_correct_sorting(order_bys, matching_runs):
    runs = [
        Run(
            run_info=RunInfo(
                run_id="9",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 121, 1, 0)], params=[Param("my_param", "A")], tags=[]
            ),
        ),
        Run(
            run_info=RunInfo(
                run_id="8",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=1,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 123, 1, 0)],
                params=[Param("my_param", "A")],
                tags=[RunTag("tag1", "C")],
            ),
        ),
        Run(
            run_info=RunInfo(
                run_id="7",
                experiment_id=1,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=1,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(
                metrics=[Metric("key1", 125, 1, 0)],
                params=[Param("my_param", "B")],
                tags=[RunTag("tag1", "D")],
            ),
        ),
    ]
    sorted_runs = SearchUtils.sort(runs, order_bys)
    sorted_run_indices = []
    for run in sorted_runs:
        for i, r in enumerate(runs):
            if r == run:
                sorted_run_indices.append(i)
                break
    assert sorted_run_indices == matching_runs


def test_order_by_metric_with_nans_infs_nones():
    metric_vals_str = ["nan", "inf", "-inf", "-1000", "0", "1000", "None"]
    runs = [
        Run(
            run_info=RunInfo(
                run_id=x,
                experiment_id=0,
                user_id="user",
                status=RunStatus.to_string(RunStatus.FINISHED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData(metrics=[Metric("x", None if x == "None" else float(x), 1, 0)]),
        )
        for x in metric_vals_str
    ]
    sorted_runs_asc = [x.info.run_id for x in SearchUtils.sort(runs, ["metrics.x asc"])]
    sorted_runs_desc = [x.info.run_id for x in SearchUtils.sort(runs, ["metrics.x desc"])]
    # asc
    assert sorted_runs_asc == ["-inf", "-1000", "0", "1000", "inf", "nan", "None"]
    # desc
    assert sorted_runs_desc == ["inf", "1000", "0", "-1000", "-inf", "nan", "None"]


@pytest.mark.parametrize(
    ("order_by", "error_message"),
    [
        ("m.acc", "Invalid entity type"),
        ("acc", "Invalid attribute key"),
        ("attri.x", "Invalid entity type"),
        ("`metrics.A", "Invalid order_by clause"),
        ("`metrics.A`", "Invalid entity type"),
        ("attribute.start", "Invalid attribute key"),
        ("attribute.experiment_id", "Invalid attribute key"),
        ("metrics.A != 1", "Invalid order_by clause"),
        ("params.my_param ", "Invalid order_by clause"),
        ("attribute.run_id ACS", "Invalid ordering key"),
        ("attribute.run_id decs", "Invalid ordering key"),
    ],
)
def test_invalid_order_by_search_runs(order_by, error_message):
    with pytest.raises(MlflowException, match=error_message):
        SearchUtils.parse_order_by_for_search_runs(order_by)


@pytest.mark.parametrize(
    ("order_by", "ascending_expected"),
    [
        ("metrics.`Mean Square Error`", True),
        ("metrics.`Mean Square Error` ASC", True),
        ("metrics.`Mean Square Error` DESC", False),
    ],
)
def test_space_order_by_search_runs(order_by, ascending_expected):
    identifier_type, identifier_name, ascending = SearchUtils.parse_order_by_for_search_runs(
        order_by
    )
    assert identifier_type == "metric"
    assert identifier_name == "Mean Square Error"
    assert ascending == ascending_expected


@pytest.mark.parametrize(
    ("order_by", "error_message"),
    [
        ("creation_timestamp DESC", "Invalid order by key"),
        ("last_updated_timestamp DESC blah", "Invalid order_by clause"),
        ("", "Invalid order_by clause"),
        ("timestamp somerandomstuff ASC", "Invalid order_by clause"),
        ("timestamp somerandomstuff", "Invalid order_by clause"),
        ("timestamp decs", "Invalid order_by clause"),
        ("timestamp ACS", "Invalid order_by clause"),
        ("name aCs", "Invalid ordering key"),
    ],
)
def test_invalid_order_by_search_registered_models(order_by, error_message):
    with pytest.raises(MlflowException, match=re.escape(error_message)):
        SearchUtils.parse_order_by_for_search_registered_models(order_by)


@pytest.mark.parametrize(
    ("page_token", "max_results", "matching_runs", "expected_next_page_token"),
    [
        (None, 1, [0], {"offset": 1}),
        (None, 2, [0, 1], {"offset": 2}),
        (None, 3, [0, 1, 2], None),
        (None, 5, [0, 1, 2], None),
        ({"offset": 1}, 1, [1], {"offset": 2}),
        ({"offset": 1}, 2, [1, 2], None),
        ({"offset": 1}, 3, [1, 2], None),
        ({"offset": 2}, 1, [2], None),
        ({"offset": 2}, 2, [2], None),
        ({"offset": 2}, 0, [], {"offset": 2}),
        ({"offset": 3}, 1, [], None),
    ],
)
def test_pagination(page_token, max_results, matching_runs, expected_next_page_token):
    runs = [
        Run(
            run_info=RunInfo(
                run_id="0",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData([], [], []),
        ),
        Run(
            run_info=RunInfo(
                run_id="1",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData([], [], []),
        ),
        Run(
            run_info=RunInfo(
                run_id="2",
                experiment_id=0,
                user_id="user-id",
                status=RunStatus.to_string(RunStatus.FAILED),
                start_time=0,
                end_time=1,
                lifecycle_stage=LifecycleStage.ACTIVE,
            ),
            run_data=RunData([], [], []),
        ),
    ]
    encoded_page_token = None
    if page_token:
        encoded_page_token = base64.b64encode(json.dumps(page_token).encode("utf-8"))
    paginated_runs, next_page_token = SearchUtils.paginate(runs, encoded_page_token, max_results)

    paginated_run_indices = []
    for run in paginated_runs:
        for i, r in enumerate(runs):
            if r == run:
                paginated_run_indices.append(i)
                break
    assert paginated_run_indices == matching_runs

    decoded_next_page_token = None
    if next_page_token:
        decoded_next_page_token = json.loads(base64.b64decode(next_page_token))
    assert decoded_next_page_token == expected_next_page_token


@pytest.mark.parametrize(
    ("page_token", "error_message"),
    [
        (base64.b64encode(json.dumps({}).encode("utf-8")), "Invalid page token"),
        (base64.b64encode(json.dumps({"offset": "a"}).encode("utf-8")), "Invalid page token"),
        (base64.b64encode(json.dumps({"offsoot": 7}).encode("utf-8")), "Invalid page token"),
        (base64.b64encode(b"not json"), "Invalid page token"),
        ("not base64", "Invalid page token"),
    ],
)
def test_invalid_page_tokens(page_token, error_message):
    with pytest.raises(MlflowException, match=error_message):
        SearchUtils.paginate([], page_token, 1)


@pytest.mark.parametrize(
    ("filter_string", "parsed_filter"),
    [
        # Boolean feedback
        (
            "feedback.is_correct = true",
            [{"comparator": "=", "key": "is_correct", "type": "feedback", "value": True}],
        ),
        (
            "feedback.is_correct = false",
            [{"comparator": "=", "key": "is_correct", "type": "feedback", "value": False}],
        ),
        (
            "feedback.is_correct != true",
            [{"comparator": "!=", "key": "is_correct", "type": "feedback", "value": True}],
        ),
        # Numeric feedback
        (
            "feedback.score = 0.95",
            [{"comparator": "=", "key": "score", "type": "feedback", "value": 0.95}],
        ),
        (
            "feedback.score > 0.5",
            [{"comparator": ">", "key": "score", "type": "feedback", "value": 0.5}],
        ),
        (
            "feedback.score < 0.5",
            [{"comparator": "<", "key": "score", "type": "feedback", "value": 0.5}],
        ),
        (
            "feedback.score >= 0.7",
            [{"comparator": ">=", "key": "score", "type": "feedback", "value": 0.7}],
        ),
        (
            "feedback.score <= 0.3",
            [{"comparator": "<=", "key": "score", "type": "feedback", "value": 0.3}],
        ),
        # String feedback
        (
            "feedback.sentiment = 'positive'",
            [{"comparator": "=", "key": "sentiment", "type": "feedback", "value": "positive"}],
        ),
        (
            'feedback.sentiment = "negative"',
            [{"comparator": "=", "key": "sentiment", "type": "feedback", "value": "negative"}],
        ),
        (
            "feedback.sentiment != 'neutral'",
            [{"comparator": "!=", "key": "sentiment", "type": "feedback", "value": "neutral"}],
        ),
        (
            "feedback.sentiment LIKE 'pos%'",
            [{"comparator": "LIKE", "key": "sentiment", "type": "feedback", "value": "pos%"}],
        ),
        (
            "feedback.category IN ('good', 'excellent')",
            [
                {
                    "comparator": "IN",
                    "key": "category",
                    "type": "feedback",
                    "value": ("good", "excellent"),
                }
            ],
        ),
        (
            "feedback.category NOT IN ('bad', 'poor')",
            [
                {
                    "comparator": "NOT IN",
                    "key": "category",
                    "type": "feedback",
                    "value": ("bad", "poor"),
                }
            ],
        ),
    ],
)
def test_trace_search_filter_with_feedback(filter_string, parsed_filter):
    from mlflow.utils.search_utils import SearchTraceUtils

    assert SearchTraceUtils.parse_search_filter_for_search_traces(filter_string) == parsed_filter


@pytest.mark.parametrize(
    ("filter_string", "error_pattern"),
    [
        # Invalid comparators for boolean values
        ("feedback.is_correct > true", "Boolean feedback values only support '=' and '!='"),
        ("feedback.is_correct < false", "Boolean feedback values only support '=' and '!='"),
        ("feedback.is_correct >= true", "Boolean feedback values only support '=' and '!='"),
        ("feedback.is_correct <= false", "Boolean feedback values only support '=' and '!='"),
        # Invalid comparators for numeric values
        (
            "feedback.score IN (0.5, 0.6)",
            "Numeric feedback values only support comparison operators",
        ),
        # Invalid comparators for string values
        ("feedback.sentiment > 'positive'", "String feedback values do not support '>'"),
        ("feedback.sentiment < 'negative'", "String feedback values do not support '<'"),
        ("feedback.sentiment >= 'positive'", "String feedback values do not support '>='"),
        ("feedback.sentiment <= 'negative'", "String feedback values do not support '<='"),
    ],
)
def test_trace_search_filter_feedback_invalid_comparators(filter_string, error_pattern):
    from mlflow.utils.search_utils import SearchTraceUtils

    with pytest.raises(MlflowException, match=error_pattern):
        SearchTraceUtils.parse_search_filter_for_search_traces(filter_string)


def test_trace_search_filter_feedback_value_type_inference():
    """Test that feedback value types are correctly inferred."""
    from mlflow.utils.search_utils import SearchTraceUtils

    # Test boolean inference
    parsed = SearchTraceUtils.parse_search_filter_for_search_traces("feedback.test = true")
    assert parsed[0]["value"] is True
    assert isinstance(parsed[0]["value"], bool)

    parsed = SearchTraceUtils.parse_search_filter_for_search_traces("feedback.test = false")
    assert parsed[0]["value"] is False
    assert isinstance(parsed[0]["value"], bool)

    # Test numeric inference
    parsed = SearchTraceUtils.parse_search_filter_for_search_traces("feedback.test = 42")
    assert parsed[0]["value"] == 42
    assert isinstance(parsed[0]["value"], int)

    parsed = SearchTraceUtils.parse_search_filter_for_search_traces("feedback.test = 3.14")
    assert parsed[0]["value"] == 3.14
    assert isinstance(parsed[0]["value"], float)

    # Test string inference
    parsed = SearchTraceUtils.parse_search_filter_for_search_traces("feedback.test = 'hello'")
    assert parsed[0]["value"] == "hello"
    assert isinstance(parsed[0]["value"], str)

    # Test list inference for IN operator
    parsed = SearchTraceUtils.parse_search_filter_for_search_traces(
        "feedback.test IN ('a', 'b', 'c')"
    )
    assert parsed[0]["value"] == ("a", "b", "c")
    assert isinstance(parsed[0]["value"], tuple)


@pytest.mark.parametrize(
    ("filter_string", "parsed_filter"),
    [
        # span.type filters
        (
            "span.type = 'LLM'",
            [{"type": "span", "key": "type", "comparator": "=", "value": "LLM"}],
        ),
        (
            "span.type != 'CHAIN'",
            [{"type": "span", "key": "type", "comparator": "!=", "value": "CHAIN"}],
        ),
        (
            "span.type IN ('LLM', 'CHAIN')",
            [{"type": "span", "key": "type", "comparator": "IN", "value": ("LLM", "CHAIN")}],
        ),
        (
            "span.type NOT IN ('UNKNOWN')",
            [{"type": "span", "key": "type", "comparator": "NOT IN", "value": ("UNKNOWN",)}],
        ),
        # span.content filters
        (
            "span.content LIKE '%hello%'",
            [{"type": "span", "key": "content", "comparator": "LIKE", "value": "%hello%"}],
        ),
        (
            "span.content ILIKE '%WORLD%'",
            [{"type": "span", "key": "content", "comparator": "ILIKE", "value": "%WORLD%"}],
        ),
    ],
)
def test_trace_search_filter_with_span(filter_string, parsed_filter):
    from mlflow.utils.search_utils import SearchTraceUtils

    assert SearchTraceUtils.parse_search_filter_for_search_traces(filter_string) == parsed_filter


@pytest.mark.parametrize(
    ("filter_string", "error_pattern"),
    [
        # Invalid comparators for span.content
        ("span.content = 'test'", "span.content only supports 'LIKE' and 'ILIKE'"),
        ("span.content > 'test'", "span.content only supports 'LIKE' and 'ILIKE'"),
        ("span.content IN ('test')", "span.content only supports 'LIKE' and 'ILIKE'"),
        ("span.content != 'test'", "span.content only supports 'LIKE' and 'ILIKE'"),
        # Invalid comparators for span.type
        ("span.type > 'LLM'", "span.type comparator '>' not one of"),
        ("span.type < 'LLM'", "span.type comparator '<' not one of"),
        ("span.type LIKE '%LLM%'", "span.type comparator 'LIKE' not one of"),
        ("span.type ILIKE '%llm%'", "span.type comparator 'ILIKE' not one of"),
        # Invalid span attributes
        ("span.invalid = 'test'", "Invalid span attribute 'invalid'"),
        ("span.name = 'test'", "Invalid span attribute 'name'"),
        ("span.status = 'OK'", "Invalid span attribute 'status'"),
    ],
)
def test_trace_search_filter_span_invalid_comparators(filter_string, error_pattern):
    from mlflow.utils.search_utils import SearchTraceUtils

    with pytest.raises(MlflowException, match=error_pattern):
        SearchTraceUtils.parse_search_filter_for_search_traces(filter_string)

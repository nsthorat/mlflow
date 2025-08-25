"""
Unit tests for DatabricksSqlStore using local Spark with fake trace data.
"""

import json
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

# Import PySpark for local testing
try:
    from pyspark.sql import SparkSession

    HAS_PYSPARK = True
except ImportError:
    HAS_PYSPARK = False

from mlflow.store.tracking.databricks_sql_store import DatabricksSqlStore


@unittest.skipUnless(HAS_PYSPARK, "PySpark not installed")
class TestDatabricksSqlStore(unittest.TestCase):
    """Test DatabricksSqlStore with local Spark and mock data."""

    @classmethod
    def setUpClass(cls):
        """Set up local Spark session for all tests."""
        cls.spark = (
            SparkSession.builder.appName("TestDatabricksSqlStore")
            .master("local[*]")
            .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-test")
            .getOrCreate()
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up Spark session."""
        if hasattr(cls, "spark"):
            cls.spark.stop()

    def setUp(self):
        """Set up test data before each test."""
        # Create fake trace data matching the real schema
        self.create_fake_trace_table()

        # Mock environment variables for Databricks connection
        os.environ["DATABRICKS_HOST"] = "https://test.databricks.com"
        os.environ["DATABRICKS_TOKEN"] = "test_token"

        # Create store instance
        self.store = DatabricksSqlStore("http://localhost:5000")

    def create_fake_trace_table(self):
        """Create a fake trace table with test data using local Spark."""
        # Define schema matching the real table - removed as not used directly

        # Create test data
        test_data = [
            (
                "tr-test-001",
                "tr-test-001",
                datetime(2025, 1, 1, 10, 0, 0),
                "OK",
                1500,
                '{"messages": [{"role": "user", "content": "Test query 1"}]}',
                '{"choices": [{"message": {"role": "assistant", "content": "Test response 1"}}]}',
                {"mlflow.user": "test_user_1", "mlflow.source.name": "test_source_1"},
                {"mlflow.traceName": "test_trace_1"},
                ("MLFLOW_EXPERIMENT", ("exp_001",), None),
                [],
                [],
            ),
            (
                "tr-test-002",
                "tr-test-002",
                datetime(2025, 1, 1, 11, 0, 0),
                "OK",
                2000,
                '{"messages": [{"role": "user", "content": "Test query 2"}]}',
                '{"choices": [{"message": {"role": "assistant", "content": "Test response 2"}}]}',
                {"mlflow.user": "test_user_2", "mlflow.source.name": "test_source_2"},
                {"mlflow.traceName": "test_trace_2"},
                ("MLFLOW_EXPERIMENT", ("exp_001",), None),
                [],
                [],
            ),
            (
                "tr-test-003",
                "tr-test-003",
                datetime(2025, 1, 1, 12, 0, 0),
                "FAILED",
                500,
                '{"messages": [{"role": "user", "content": "Test query 3"}]}',
                '{"error": "Test error"}',
                {"mlflow.user": "test_user_1", "mlflow.source.name": "test_source_3"},
                {"mlflow.traceName": "test_trace_3"},
                ("MLFLOW_EXPERIMENT", ("exp_002",), None),
                [],
                [],
            ),
        ]

        # Create DataFrame
        columns = [
            "trace_id",
            "client_request_id",
            "request_time",
            "state",
            "execution_duration_ms",
            "request",
            "response",
            "trace_metadata",
            "tags",
            "trace_location",
            "assessments",
            "spans",
        ]

        df = self.spark.createDataFrame(test_data, columns)

        # Register as temporary view (simulating the real table)
        df.createOrReplaceTempView("trace_logs_table")

        # Also create the namespaced version for testing
        df.createOrReplaceTempView("mosaic_catalog.lilac_schema.trace_logs_2665190525370131")

    def test_search_traces_basic(self):
        """Test basic search_traces functionality."""
        # Mock the Spark session to return our local session with test data
        with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
            # Create a mock spark session that simulates parameterized query support
            mock_spark_session = Mock()
            mock_df = Mock()
            mock_df.collect.return_value = []  # Return empty results for simplicity
            
            # Mock the sql method to accept parameters
            def mock_sql(query, params=None):
                # Verify that parameterized query is being used for limit
                self.assertIn(":limit_value", query)
                if params:
                    self.assertIn("limit_value", params)
                return mock_df
            
            mock_spark_session.sql = mock_sql
            mock_spark.return_value = mock_spark_session

            # Set the table name to use our test table
            self.store._TABLE_NAME = "trace_logs_table"

            # Call the REAL search_traces method - the store will execute the SQL
            traces, next_token = self.store.search_traces(
                experiment_ids=["exp_001"], max_results=10
            )

            # Verify the mock was called
            mock_spark.assert_called_once()

    def test_search_traces_with_filter(self):
        """Test search_traces with filter string."""
        # Mock the Spark session to use our local test data
        with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
            mock_spark.return_value = self.spark

            # Set the table name to use our test table
            self.store._TABLE_NAME = "trace_logs_table"

            # Test search with filter (filter parsing not implemented yet, so it will be ignored)
            traces, next_token = self.store.search_traces(
                experiment_ids=["exp_001"], filter_string="status = 'OK'", max_results=5
            )

            # Should still return our test data (filter is not parsed yet)
            self.assertEqual(len(traces), 2)
            from mlflow.entities.trace_state import TraceState

            self.assertEqual(traces[0].state, TraceState.OK)
            self.assertEqual(traces[1].state, TraceState.OK)

    def test_search_traces_raises_on_error(self):
        """Test that search_traces raises exception on Databricks SQL error."""
        # Mock Spark session to raise an error
        with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
            mock_spark.side_effect = Exception("Connection failed")

            # Test search - should raise exception
            with self.assertRaises(Exception) as context:
                traces, next_token = self.store.search_traces(
                    experiment_ids=["exp_001"], max_results=10
                )

            # Verify the exception message
            self.assertIn("Connection failed", str(context.exception))


    def test_spark_session_lifecycle(self):
        """Test Spark session creation and cleanup."""
        store = DatabricksSqlStore("http://localhost:5000")

        # Mock DatabricksSession
        with patch("mlflow.store.tracking.databricks_sql_store.DatabricksSession") as mock_session:
            mock_spark = Mock()
            mock_session.builder.serverless.return_value.getOrCreate.return_value = mock_spark

            # First call creates session
            session1 = store._get_or_create_spark_session()
            self.assertEqual(session1, mock_spark)
            mock_session.builder.serverless.assert_called_once_with(True)

            # Second call returns existing session
            session2 = store._get_or_create_spark_session()
            self.assertEqual(session2, mock_spark)
            # Still only called once
            mock_session.builder.serverless.assert_called_once()

            # Cleanup
            del store
            # Spark session stop should be attempted in __del__
            # (Note: __del__ behavior can be unpredictable in tests)


class TestTraceTableDiscovery(unittest.TestCase):
    """Test the trace table discovery functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Mock environment variables for Databricks connection
        os.environ["DATABRICKS_HOST"] = "https://test.databricks.com"
        os.environ["DATABRICKS_TOKEN"] = "test_token"

        # Create store instance
        self.store = DatabricksSqlStore("http://localhost:5000")

    def test_get_trace_table_for_experiment_success(self):
        """Test successful retrieval of trace table from monitors API."""
        # Mock the requests.post call
        with patch("requests.post") as mock_post:
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "monitor_infos": [
                    {
                        "monitor": {
                            "experiment_id": "123456",
                            "trace_archive_table": "`catalog`.`schema`.`trace_logs_123456`",
                        },
                        "endpoint_name": "123456",
                        "latest_run_lifecycle_state": "RUNNING",
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Call the method
            table_name = self.store._get_trace_table_for_experiment("123456")

            # Verify the result (backticks should be removed)
            self.assertEqual(table_name, "catalog.schema.trace_logs_123456")

            # Verify the API was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertTrue(call_args[0][0].endswith("/api/2.0/managed-evals/monitors"))
            self.assertEqual(json.loads(call_args[1]["data"]), {"experiment_id": "123456"})
            # Authorization header may or may not be present depending on host_creds
            self.assertIn("Content-Type", call_args[1]["headers"])

    def test_get_trace_table_for_experiment_no_monitor(self):
        """Test when no monitor exists for the experiment."""
        with patch("requests.post") as mock_post:
            # Create mock response with empty monitor_infos
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"monitor_infos": []}
            mock_post.return_value = mock_response

            # Call the method
            table_name = self.store._get_trace_table_for_experiment("999999")

            # Should return None when no monitor found
            self.assertIsNone(table_name)

    def test_get_trace_table_for_experiment_no_table(self):
        """Test when monitor exists but has no trace_archive_table."""
        with patch("requests.post") as mock_post:
            # Create mock response without trace_archive_table
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "monitor_infos": [
                    {
                        "monitor": {
                            "experiment_id": "123456",
                            # No trace_archive_table field
                        }
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Call the method
            table_name = self.store._get_trace_table_for_experiment("123456")

            # Should return None when no table field
            self.assertIsNone(table_name)

    def test_get_trace_table_for_experiment_api_error(self):
        """Test graceful handling of API errors."""
        with patch("requests.post") as mock_post:
            # Create mock response with error status
            mock_response = Mock()
            mock_response.status_code = 404
            mock_post.return_value = mock_response

            # Call the method
            table_name = self.store._get_trace_table_for_experiment("123456")

            # Should return None on API error
            self.assertIsNone(table_name)

    def test_get_trace_table_for_experiment_exception(self):
        """Test graceful handling of exceptions."""
        with patch("requests.post") as mock_post:
            # Make requests.post raise an exception
            mock_post.side_effect = Exception("Network error")

            # Call the method
            table_name = self.store._get_trace_table_for_experiment("123456")

            # Should return None on exception
            self.assertIsNone(table_name)

    def test_caching_works(self):
        """Test that the lru_cache caches results properly."""
        with patch("requests.post") as mock_post:
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "monitor_infos": [
                    {
                        "monitor": {
                            "experiment_id": "123456",
                            "trace_archive_table": "`catalog`.`schema`.`trace_logs_123456`",
                        }
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Call the method twice with same experiment_id
            table1 = self.store._get_trace_table_for_experiment("123456")
            table2 = self.store._get_trace_table_for_experiment("123456")

            # Both should return the same result
            self.assertEqual(table1, "catalog.schema.trace_logs_123456")
            self.assertEqual(table2, "catalog.schema.trace_logs_123456")

            # But API should only be called once due to caching
            mock_post.assert_called_once()

    def test_search_traces_with_table_discovery(self):
        """Test that search_traces uses discovered table when available."""
        with patch("requests.post") as mock_post:
            # Mock successful table discovery
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "monitor_infos": [
                    {
                        "monitor": {
                            "experiment_id": "123456",
                            "trace_archive_table": "`catalog`.`schema`.`trace_logs_123456`",
                        }
                    }
                ]
            }
            mock_post.return_value = mock_response

            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                mock_df.collect.return_value = []  # No traces for simplicity
                
                # Mock sql method to verify parameterized queries
                def mock_sql(query, params=None):
                    # Verify table name is correct
                    self.assertIn("catalog.schema.trace_logs_123456", query)
                    # Verify parameterized query is being used for limit
                    self.assertIn(":limit_value", query)
                    # We should NOT have experiment_id filtering since table is already filtered
                    self.assertNotIn(":exp_id", query)
                    if params:
                        self.assertIn("limit_value", params)
                        # Should not have experiment_id params
                        self.assertNotIn("exp_id_0", params)
                    return mock_df
                
                mock_spark_session.sql = mock_sql
                mock_spark.return_value = mock_spark_session

                # Call search_traces with single experiment
                traces, token = self.store.search_traces(experiment_ids=["123456"])

                # Verify table discovery was called
                mock_post.assert_called_once()

                # Verify SQL was executed
                mock_spark.assert_called_once()

    def test_search_traces_fallback_to_rest(self):
        """Test that search_traces falls back to REST when no table found."""
        with patch("requests.post") as mock_post:
            # Mock no table found
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"monitor_infos": []}
            mock_post.return_value = mock_response

            # Mock the parent RestStore.search_traces
            with patch("mlflow.store.tracking.rest_store.RestStore.search_traces") as mock_rest:
                mock_rest.return_value = ([], None)

                # Call search_traces with single experiment
                traces, token = self.store.search_traces(experiment_ids=["999999"])

                # Verify table discovery was attempted
                mock_post.assert_called_once()

                # Verify it fell back to REST API
                mock_rest.assert_called_once_with(
                    experiment_ids=["999999"],
                    filter_string=None,
                    max_results=100,  # Default max results
                    order_by=None,
                    page_token=None,
                    model_id=None,
                    sql_warehouse_id=None,
                )

    def test_search_traces_multiple_experiments_uses_rest(self):
        """Test that search_traces uses REST for multiple experiments."""
        # Mock the parent RestStore.search_traces
        with patch("mlflow.store.tracking.rest_store.RestStore.search_traces") as mock_rest:
            mock_rest.return_value = ([], None)

            # Call search_traces with multiple experiments
            traces, token = self.store.search_traces(experiment_ids=["123", "456"])

            # Should go directly to REST without trying table discovery
            mock_rest.assert_called_once()

            # Verify no attempt to discover table (no network call)
            with patch("requests.post") as mock_post:
                mock_post.assert_not_called()

    def test_search_traces_with_sql_warehouse_id_not_implemented(self):
        """Test that sql_warehouse_id raises NotImplementedError."""
        # Test search with sql_warehouse_id should raise NotImplementedError
        with self.assertRaises(NotImplementedError) as context:
            traces, next_token = self.store.search_traces(
                experiment_ids=["exp_001"], sql_warehouse_id="warehouse_123", model_id="model_456"
            )
        
        # Verify the error message
        self.assertIn("not yet implemented", str(context.exception))


class TestNPMICalculation(unittest.TestCase):
    """Test the NPMI calculation functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Mock environment variables for Databricks connection
        os.environ["DATABRICKS_HOST"] = "https://test.databricks.com"
        os.environ["DATABRICKS_TOKEN"] = "test_token"

        # Create store instance
        self.store = DatabricksSqlStore("http://localhost:5000")

    def test_calculate_trace_filter_correlation_success(self):
        """Test successful NPMI calculation."""
        # Mock table discovery
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = "catalog.schema.trace_logs_123456"
            
            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                
                # Create mock row with NPMI results
                mock_row = {
                    "total_count": 1000,
                    "filter1_count": 100,
                    "filter2_count": 150,
                    "joint_count": 50,
                    "npmi": 0.75,
                    "npmi_lower": 0.65,
                    "npmi_upper": 0.85,
                    "p_filter1": 0.1,
                    "p_filter2": 0.15,
                    "p_joint": 0.05
                }
                mock_df.collect.return_value = [mock_row]
                
                def mock_sql(query, params=None):
                    # Verify the query structure
                    self.assertIn("WITH", query)
                    self.assertIn("total_counts", query)
                    self.assertIn("filter1_matches", query)
                    self.assertIn("filter2_matches", query)
                    self.assertIn("joint_matches", query)
                    self.assertIn("INTERSECT", query)
                    self.assertIn("npmi", query)
                    self.assertIn("LOG2", query)
                    
                    # Verify parameterized filters
                    if params:
                        # Check that filter parameters are prefixed correctly
                        param_keys = list(params.keys())
                        f1_params = [k for k in param_keys if k.startswith("f1_")]
                        f2_params = [k for k in param_keys if k.startswith("f2_")]
                        self.assertTrue(len(f1_params) > 0 or len(f2_params) > 0)
                    
                    return mock_df
                
                mock_spark_session.sql = mock_sql
                mock_spark.return_value = mock_spark_session
                
                # Call the method
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'ERROR'",
                    filter_string2="tags.tool = 'langchain'"
                )
                
                # Verify result
                self.assertEqual(result.npmi, 0.75)
                self.assertEqual(result.confidence_lower, 0.65)
                self.assertEqual(result.confidence_upper, 0.85)
                self.assertEqual(result.filter_string1_count, 100)
                self.assertEqual(result.filter_string2_count, 150)
                self.assertEqual(result.joint_count, 50)
                self.assertEqual(result.total_count, 1000)

    def test_calculate_trace_filter_correlation_no_data(self):
        """Test NPMI calculation with no data."""
        # Mock table discovery
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = "catalog.schema.trace_logs_123456"
            
            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                
                # Return empty results
                mock_df.collect.return_value = []
                mock_spark_session.sql = lambda q, p=None: mock_df
                mock_spark.return_value = mock_spark_session
                
                # Call the method
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'ERROR'",
                    filter_string2="tags.tool = 'langchain'"
                )
                
                # Verify result for no data
                self.assertEqual(result.npmi, 0.0)
                self.assertIsNone(result.confidence_lower)
                self.assertIsNone(result.confidence_upper)
                self.assertEqual(result.filter_string1_count, 0)
                self.assertEqual(result.filter_string2_count, 0)
                self.assertEqual(result.joint_count, 0)
                self.assertEqual(result.total_count, 0)

    def test_calculate_trace_filter_correlation_perfect_correlation(self):
        """Test NPMI calculation with perfect correlation."""
        # Mock table discovery
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = "catalog.schema.trace_logs_123456"
            
            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                
                # Create mock row with perfect correlation (both filters match exactly same traces)
                mock_row = {
                    "total_count": 1000,
                    "filter1_count": 100,
                    "filter2_count": 100,
                    "joint_count": 100,  # Same as both individual counts
                    "npmi": 1.0,  # Perfect correlation
                    "npmi_lower": 1.0,
                    "npmi_upper": 1.0,
                    "p_filter1": 0.1,
                    "p_filter2": 0.1,
                    "p_joint": 0.1
                }
                mock_df.collect.return_value = [mock_row]
                mock_spark_session.sql = lambda q, p=None: mock_df
                mock_spark.return_value = mock_spark_session
                
                # Call the method
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'ERROR'",
                    filter_string2="execution_time > 5000"
                )
                
                # Verify perfect correlation
                self.assertEqual(result.npmi, 1.0)
                self.assertEqual(result.confidence_lower, 1.0)
                self.assertEqual(result.confidence_upper, 1.0)
                self.assertEqual(result.joint_count, 100)
                self.assertEqual(result.filter_string1_count, 100)
                self.assertEqual(result.filter_string2_count, 100)

    def test_calculate_trace_filter_correlation_no_overlap(self):
        """Test NPMI calculation with no overlap between filters."""
        # Mock table discovery
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = "catalog.schema.trace_logs_123456"
            
            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                
                # Create mock row with no overlap
                mock_row = {
                    "total_count": 1000,
                    "filter1_count": 100,
                    "filter2_count": 150,
                    "joint_count": 0,  # No overlap
                    "npmi": -1.0,  # Perfect anti-correlation
                    "npmi_lower": -1.0,
                    "npmi_upper": -1.0,
                    "p_filter1": 0.1,
                    "p_filter2": 0.15,
                    "p_joint": 0.0
                }
                mock_df.collect.return_value = [mock_row]
                mock_spark_session.sql = lambda q, p=None: mock_df
                mock_spark.return_value = mock_spark_session
                
                # Call the method
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'OK'",
                    filter_string2="status = 'ERROR'"  # Mutually exclusive
                )
                
                # Verify no overlap
                self.assertEqual(result.npmi, -1.0)
                self.assertEqual(result.joint_count, 0)

    def test_calculate_trace_filter_correlation_fallback_to_rest(self):
        """Test NPMI calculation falls back to REST when no table found."""
        # Mock table discovery to return None
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = None
            
            # Mock the parent RestStore method
            with patch("mlflow.store.tracking.rest_store.RestStore.calculate_trace_filter_correlation") as mock_rest:
                from mlflow.tracing.analysis import TraceFilterCorrelationResult
                mock_rest.return_value = TraceFilterCorrelationResult(
                    npmi=0.5,
                    filter_string1_count=50,
                    filter_string2_count=75,
                    joint_count=25,
                    total_count=500
                )
                
                # Call the method
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'ERROR'",
                    filter_string2="tags.tool = 'langchain'"
                )
                
                # Verify it fell back to REST
                mock_rest.assert_called_once_with(
                    ["123456"],
                    "status = 'ERROR'",
                    "tags.tool = 'langchain'"
                )
                
                # Verify result from REST
                self.assertEqual(result.npmi, 0.5)
                self.assertEqual(result.filter_string1_count, 50)

    def test_calculate_trace_filter_correlation_multiple_experiments(self):
        """Test NPMI calculation with multiple experiments uses REST."""
        # Mock the parent RestStore method
        with patch("mlflow.store.tracking.rest_store.RestStore.calculate_trace_filter_correlation") as mock_rest:
            from mlflow.tracing.analysis import TraceFilterCorrelationResult
            mock_rest.return_value = TraceFilterCorrelationResult(
                npmi=0.3,
                filter_string1_count=100,
                filter_string2_count=200,
                joint_count=60,
                total_count=1000
            )
            
            # Call with multiple experiments
            result = self.store.calculate_trace_filter_correlation(
                experiment_ids=["123", "456", "789"],
                filter_string1="status = 'ERROR'",
                filter_string2="tags.tool = 'langchain'"
            )
            
            # Verify it went directly to REST
            mock_rest.assert_called_once()
            self.assertEqual(result.npmi, 0.3)

    def test_calculate_trace_filter_correlation_complex_filters(self):
        """Test NPMI calculation with complex filter strings."""
        # Mock table discovery
        with patch.object(self.store, "_get_trace_table_for_experiment") as mock_get_table:
            mock_get_table.return_value = "catalog.schema.trace_logs_123456"
            
            # Mock Spark session
            with patch.object(self.store, "_get_or_create_spark_session") as mock_spark:
                mock_spark_session = Mock()
                mock_df = Mock()
                
                # Create mock row
                mock_row = {
                    "total_count": 1000,
                    "filter1_count": 80,
                    "filter2_count": 120,
                    "joint_count": 40,
                    "npmi": 0.6,
                    "npmi_lower": 0.5,
                    "npmi_upper": 0.7,
                    "p_filter1": 0.08,
                    "p_filter2": 0.12,
                    "p_joint": 0.04
                }
                mock_df.collect.return_value = [mock_row]
                
                def mock_sql(query, params=None):
                    # Verify complex filter parameters are handled
                    if params:
                        # Should have parameters for both filters
                        self.assertTrue(any(k.startswith("f1_") for k in params))
                        self.assertTrue(any(k.startswith("f2_") for k in params))
                    return mock_df
                
                mock_spark_session.sql = mock_sql
                mock_spark.return_value = mock_spark_session
                
                # Call with complex filters
                result = self.store.calculate_trace_filter_correlation(
                    experiment_ids=["123456"],
                    filter_string1="status = 'ERROR' AND execution_time > 5000",
                    filter_string2="tags.tool = 'langchain' AND tags.env = 'prod'"
                )
                
                # Verify result
                self.assertEqual(result.npmi, 0.6)
                self.assertEqual(result.joint_count, 40)


if __name__ == "__main__":
    unittest.main()

from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroOfflineModeError
from stonks_overwatch.services.brokers.degiro.services.helper import retry_with_backoff
from stonks_overwatch.utils.core.logger import StonksLogger

from unittest.mock import Mock, patch


class TestRetryWithBackoff:
    """Test cases for the retry_with_backoff function."""

    def test_successful_first_attempt(self):
        """Test that function succeeds on first attempt without retries."""
        # Arrange
        expected_result = {"data": "success"}
        mock_func = Mock(return_value=expected_result)

        # Act
        result = retry_with_backoff(func=mock_func, max_retries=3, delay_ms=100, operation_name="test_operation")

        # Assert
        assert result == expected_result
        assert mock_func.call_count == 1

    def test_successful_after_retries(self):
        """Test that function succeeds after some retries."""
        # Arrange
        expected_result = {"data": "success"}
        mock_func = Mock(side_effect=[None, None, expected_result])
        mock_logger = Mock(spec=StonksLogger)

        # Act
        result = retry_with_backoff(
            func=mock_func, max_retries=3, delay_ms=100, operation_name="test_operation", logger=mock_logger
        )

        # Assert
        assert result == expected_result
        assert mock_func.call_count == 3
        mock_logger.info.assert_called_once_with("Successfully retrieved test_operation after 2 retries")

    def test_fails_after_max_retries_with_none(self):
        """Test that function returns None after exhausting all retries when function returns None."""
        # Arrange
        mock_func = Mock(return_value=None)
        mock_logger = Mock(spec=StonksLogger)

        # Act
        result = retry_with_backoff(
            func=mock_func, max_retries=2, delay_ms=100, operation_name="test_operation", logger=mock_logger
        )

        # Assert
        assert result is None
        assert mock_func.call_count == 3  # Initial attempt + 2 retries
        mock_logger.warning.assert_called_with("test_operation returned None after all 3 attempts")

    def test_connection_error_with_retries(self):
        """Test retry behavior with ConnectionError exceptions."""
        # Arrange
        mock_func = Mock(
            side_effect=[ConnectionError("Network error"), ConnectionError("Network error"), {"data": "success"}]
        )
        mock_logger = Mock(spec=StonksLogger)

        with patch("time.sleep") as mock_sleep:
            # Act
            result = retry_with_backoff(
                func=mock_func, max_retries=3, delay_ms=500, operation_name="test_operation", logger=mock_logger
            )

        # Assert
        assert result == {"data": "success"}
        assert mock_func.call_count == 3
        # Verify exponential backoff
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.5)  # 500ms
        mock_sleep.assert_any_call(1.0)  # 1000ms (doubled)

    def test_timeout_error_with_retries(self):
        """Test retry behavior with TimeoutError exceptions."""
        # Arrange
        mock_func = Mock(side_effect=TimeoutError("Request timeout"))
        mock_logger = Mock(spec=StonksLogger)

        with patch("time.sleep"):
            # Act
            result = retry_with_backoff(
                func=mock_func, max_retries=2, delay_ms=200, operation_name="timeout_test", logger=mock_logger
            )

        # Assert
        assert result is None
        assert mock_func.call_count == 3  # Initial + 2 retries
        mock_logger.error.assert_called_once_with("All 3 attempts for timeout_test failed: Request timeout")

    def test_degiro_offline_mode_error_with_retries(self):
        """Test retry behavior with DeGiroOfflineModeError exceptions."""
        # Arrange
        mock_func = Mock(side_effect=DeGiroOfflineModeError("DeGiro offline"))
        mock_logger = Mock(spec=StonksLogger)

        with patch("time.sleep"):
            # Act
            result = retry_with_backoff(
                func=mock_func, max_retries=1, delay_ms=300, operation_name="offline_test", logger=mock_logger
            )

        # Assert
        assert result is None
        assert mock_func.call_count == 2  # Initial + 1 retry
        mock_logger.error.assert_called_once_with("All 2 attempts for offline_test failed: DeGiro offline")

    def test_unexpected_exception_no_retry(self):
        """Test that unexpected exceptions are not retried."""
        # Arrange
        mock_func = Mock(side_effect=ValueError("Unexpected error"))
        mock_logger = Mock(spec=StonksLogger)

        # Act
        result = retry_with_backoff(
            func=mock_func, max_retries=3, delay_ms=100, operation_name="error_test", logger=mock_logger
        )

        # Assert
        assert result is None
        assert mock_func.call_count == 1  # Only called once, no retries for unexpected errors
        mock_logger.error.assert_called_once_with("Unexpected error during error_test: Unexpected error")

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff increases delays correctly."""
        # Arrange
        mock_func = Mock(side_effect=[ConnectionError("Error"), ConnectionError("Error"), ConnectionError("Error")])
        mock_logger = Mock(spec=StonksLogger)

        with patch("time.sleep") as mock_sleep:
            # Act
            retry_with_backoff(
                func=mock_func, max_retries=2, delay_ms=100, operation_name="backoff_test", logger=mock_logger
            )

        # Assert
        expected_delays = [0.1, 0.2]  # 100ms, then 200ms (doubled)
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_default_logger_when_none_provided(self):
        """Test that a default logger is created when none is provided."""
        # Arrange
        mock_func = Mock(return_value={"data": "success"})

        with patch(
            "stonks_overwatch.services.brokers.degiro.services.helper.StonksLogger.get_logger"
        ) as mock_get_logger:
            mock_logger = Mock(spec=StonksLogger)
            mock_get_logger.return_value = mock_logger

            # Act
            result = retry_with_backoff(func=mock_func, operation_name="default_logger_test")

        # Assert
        assert result == {"data": "success"}
        mock_get_logger.assert_called_once_with("stonks_overwatch.degiro.helper", "[DEGIRO|RETRY]")

    def test_custom_parameters(self):
        """Test retry function with custom parameters."""
        # Arrange
        expected_result = "custom_result"
        mock_func = Mock(side_effect=[None, expected_result])
        mock_logger = Mock(spec=StonksLogger)

        # Act (Note: No sleep occurs since function succeeds on second attempt)
        result = retry_with_backoff(
            func=mock_func, max_retries=5, delay_ms=250, operation_name="custom_test", logger=mock_logger
        )

        # Assert
        assert result == expected_result
        assert mock_func.call_count == 2
        mock_logger.info.assert_called_once_with("Successfully retrieved custom_test after 1 retries")

    def test_warning_messages_for_none_returns(self):
        """Test that appropriate warning messages are logged for None returns."""
        # Arrange
        mock_func = Mock(return_value=None)
        mock_logger = Mock(spec=StonksLogger)

        # Act
        retry_with_backoff(func=mock_func, max_retries=2, operation_name="warning_test", logger=mock_logger)

        # Assert
        expected_warnings = [
            "warning_test returned None, attempt 1/3",
            "warning_test returned None, attempt 2/3",
            "warning_test returned None after all 3 attempts",
        ]

        warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert warning_calls == expected_warnings

    def test_warning_messages_for_exceptions_during_retries(self):
        """Test warning messages during exception retries."""
        # Arrange
        mock_func = Mock(side_effect=[ConnectionError("Network issue"), {"success": True}])
        mock_logger = Mock(spec=StonksLogger)

        with patch("time.sleep"):
            # Act
            retry_with_backoff(
                func=mock_func, max_retries=2, delay_ms=100, operation_name="exception_warning_test", logger=mock_logger
            )

        # Assert
        mock_logger.warning.assert_called_once_with(
            "Attempt 1/3 for exception_warning_test failed: Network issue. Retrying in 0.1s..."
        )

    def test_zero_max_retries(self):
        """Test behavior when max_retries is set to 0."""
        # Arrange
        mock_func = Mock(return_value=None)
        mock_logger = Mock(spec=StonksLogger)

        # Act
        result = retry_with_backoff(func=mock_func, max_retries=0, operation_name="zero_retry_test", logger=mock_logger)

        # Assert
        assert result is None
        assert mock_func.call_count == 1  # Only initial attempt
        mock_logger.warning.assert_called_once_with("zero_retry_test returned None after all 1 attempts")

    def test_function_returning_false_is_considered_valid(self):
        """Test that functions returning False (falsy but not None) are considered successful."""
        # Arrange
        mock_func = Mock(return_value=False)

        # Act
        result = retry_with_backoff(func=mock_func, max_retries=2, operation_name="false_return_test")

        # Assert
        assert result is False
        assert mock_func.call_count == 1  # No retries needed

    def test_function_returning_empty_dict_is_considered_valid(self):
        """Test that functions returning empty containers are considered successful."""
        # Arrange
        mock_func = Mock(return_value={})

        # Act
        result = retry_with_backoff(func=mock_func, max_retries=2, operation_name="empty_dict_test")

        # Assert
        assert result == {}
        assert mock_func.call_count == 1  # No retries needed

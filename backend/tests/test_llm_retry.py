import pytest
from unittest.mock import MagicMock
from ai_pipeline.llm import get_llm, call_with_retry


class MockError429:
    def __init__(self):
        self.status_code = 429


class MockErrorWithResponse:
    def __init__(self, status_code):
        self.response = MagicMock()
        self.response.status_code = status_code


class TestCallWithRetry:
    def test_retry_on_429_twice_then_succeed(self):
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            if call_count[0] <= 2:
                error = MockError429()
                raise Exception() from Exception()
            return "success"
        
        error = MockError429()
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            if call_count[0] <= 2:
                exc = Exception("Rate limited")
                exc.status_code = 429
                raise exc
            return "success"
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        result = call_with_retry(mock_fn, sleep_fn=mock_sleep)
        
        assert result == "success"
        assert len(sleep_calls) == 2
        assert all(10 <= d <= 20 for d in sleep_calls)

    def test_429_three_times_raises(self):
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            exc = Exception("Rate limited")
            exc.status_code = 429
            raise exc
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        with pytest.raises(Exception):
            call_with_retry(mock_fn, sleep_fn=mock_sleep)
        
        assert call_count[0] == 3
        assert len(sleep_calls) == 2

    def test_non_429_error_raises_immediately(self):
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            exc = Exception("Some other error")
            exc.status_code = 500
            raise exc
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        with pytest.raises(Exception):
            call_with_retry(mock_fn, sleep_fn=mock_sleep)
        
        assert call_count[0] == 1
        assert len(sleep_calls) == 0

    def test_sleep_durations_in_range(self):
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            if call_count[0] <= 2:
                exc = Exception("Rate limited")
                exc.status_code = 429
                raise exc
            return "success"
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        call_with_retry(mock_fn, sleep_fn=mock_sleep)
        
        assert len(sleep_calls) == 2
        for duration in sleep_calls:
            assert 10 <= duration <= 20

    def test_429_with_response_attribute(self):
        call_count = [0]
        sleep_calls = []
        
        def mock_fn():
            call_count[0] += 1
            if call_count[0] <= 1:
                exc = Exception("Rate limited")
                exc.response = MagicMock()
                exc.response.status_code = 429
                raise exc
            return "success"
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        result = call_with_retry(mock_fn, sleep_fn=mock_sleep)
        
        assert result == "success"
        assert len(sleep_calls) == 1


class TestGetLLM:
    def test_get_llm_returns_chatgroq(self):
        llm = get_llm("test-model")
        assert llm.model_name == "test-model"
        assert llm.temperature < 0.001
        assert llm.request_timeout == 30
        assert llm.max_retries == 0

    def test_get_llm_with_different_models(self):
        llm1 = get_llm("model-1")
        llm2 = get_llm("model-2")
        
        assert llm1.model_name == "model-1"
        assert llm2.model_name == "model-2"
        assert llm1.temperature < 0.001
        assert llm2.temperature < 0.001

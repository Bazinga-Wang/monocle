import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanContext
from opentelemetry.trace.propagation import get_current_span
import uuid
import random
from monocle_apptrace.instrumentation.common.instrumentor import (
    MonocleInstrumentor,
    set_tracer_provider,
    get_tracer_provider,
    setup_monocle_telemetry,
    on_processor_start,
    set_context_properties,
    propagate_trace_id,
    propagate_trace_id_from_traceparent,
    stop_propagate_trace_id,
    is_valid_trace_id_uuid,
    start_scope,
    stop_scope,
    monocle_trace_scope,
    monocle_trace_scope_method,
    monocle_trace_http_route,
    FixedIdGenerator
)

@pytest.fixture
def mock_tracer_provider():
    provider = Mock(spec=TracerProvider)
    return provider

@pytest.fixture
def mock_span():
    span = Mock(spec=Span)
    span.get_span_context.return_value = Mock(spec=SpanContext)
    return span

@pytest.fixture
def mock_span_handler():
    handler = Mock()
    return handler

def test_set_get_tracer_provider(mock_tracer_provider):
    set_tracer_provider(mock_tracer_provider)
    assert get_tracer_provider() == mock_tracer_provider

def test_setup_monocle_telemetry():
    workflow_name = "test_workflow"
    mock_processor = Mock(spec=BatchSpanProcessor)
    mock_provider = Mock(spec=TracerProvider)
    mock_exporter = Mock()
    mock_exporter.return_value = [Mock()]

    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_monocle_exporter', return_value=[mock_exporter]), \
         patch('monocle_apptrace.instrumentation.common.instrumentor.TracerProvider', return_value=mock_provider), \
         patch('monocle_apptrace.instrumentation.common.instrumentor.trace') as mock_trace:

        mock_trace.get_tracer_provider.return_value = mock_provider

        instrumentor = setup_monocle_telemetry(
            workflow_name=workflow_name,
            span_processors=[mock_processor]
        )

        assert isinstance(instrumentor, MonocleInstrumentor)
        mock_provider.add_span_processor.assert_called_with(mock_processor)

def test_on_processor_start(mock_span):
    test_properties = {"key": "value"}
    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_value') as mock_get_value:
        mock_get_value.return_value = test_properties
        on_processor_start(mock_span, None)
        mock_span.set_attribute.assert_called_once_with("session.key", "value")

def test_set_context_properties():
    test_properties = {"key": "value"}
    with patch('monocle_apptrace.instrumentation.common.instrumentor.attach') as mock_attach:
        set_context_properties(test_properties)
        mock_attach.assert_called_once()

def test_propagate_trace_id():
    test_trace_id = str(uuid.uuid4())
    mock_tracer = Mock()
    mock_span = Mock()
    mock_tracer.start_span.return_value = mock_span
    mock_span.get_span_context.return_value = Mock()

    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_tracer', return_value=mock_tracer):
        token = propagate_trace_id(test_trace_id)
        assert token is not None

def test_propagate_trace_id_with_0x():
    test_trace_id = "0x" + str(uuid.uuid4()).replace("-", "")
    mock_tracer = Mock()
    mock_span = Mock()
    mock_tracer.start_span.return_value = mock_span
    mock_span.get_span_context.return_value = Mock()

    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_tracer', return_value=mock_tracer):
        token = propagate_trace_id(test_trace_id)
        assert token is not None

def test_propagate_trace_id_invalid():
    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_tracer') as mock_get_tracer:
        mock_get_tracer.side_effect = Exception("Invalid trace ID")
        token = propagate_trace_id("invalid-trace-id")
        assert token is None

def test_stop_propagate_trace_id():
    mock_token = Mock()
    with patch('monocle_apptrace.instrumentation.common.instrumentor.detach') as mock_detach:
        stop_propagate_trace_id(mock_token)
        mock_detach.assert_called_once_with(mock_token)

def test_is_valid_trace_id_uuid():
    valid_id = str(uuid.uuid4())
    assert is_valid_trace_id_uuid(valid_id) is True
    assert is_valid_trace_id_uuid("invalid-id") is False

def test_start_stop_scope():
    with patch('monocle_apptrace.instrumentation.common.instrumentor.set_scope') as mock_set_scope:
        mock_token = Mock()
        mock_set_scope.return_value = mock_token

        token = start_scope("test_scope", "test_value")
        assert token == mock_token

        with patch('monocle_apptrace.instrumentation.common.instrumentor.remove_scope') as mock_remove_scope:
            stop_scope(token)
            mock_remove_scope.assert_called_once_with(token)

def test_monocle_trace_scope():
    with patch('monocle_apptrace.instrumentation.common.instrumentor.start_scope') as mock_start_scope:
        mock_token = Mock()
        mock_start_scope.return_value = mock_token

        with patch('monocle_apptrace.instrumentation.common.instrumentor.stop_scope') as mock_stop_scope:
            with monocle_trace_scope("test_scope", "test_value"):
                pass

            mock_start_scope.assert_called_once()
            mock_stop_scope.assert_called_once_with(mock_token)

@pytest.mark.asyncio
async def test_monocle_trace_scope_method_async():
    @monocle_trace_scope_method("test_scope")
    async def test_func():
        return "result"

    result = await test_func()
    assert result == "result"

def test_monocle_trace_scope_method_sync():
    @monocle_trace_scope_method("test_scope")
    def test_func():
        return "result"

    result = test_func()
    assert result == "result"

def test_fixed_id_generator():
    trace_id = random.getrandbits(64)
    generator = FixedIdGenerator(trace_id)

    assert generator.generate_trace_id() == trace_id
    assert isinstance(generator.generate_span_id(), int)

def test_monocle_instrumentor_basic(mock_span_handler):
    handlers = {"default": mock_span_handler}
    instrumentor = MonocleInstrumentor(handlers=handlers)
    assert instrumentor.handlers["default"] == mock_span_handler

def test_monocle_instrumentor_with_default_handlers():
    instrumentor = MonocleInstrumentor(handlers=None)
    assert "default" in instrumentor.handlers

@pytest.mark.asyncio
async def test_monocle_trace_http_route_async():
    @monocle_trace_http_route
    async def test_route():
        return "response"

    result = await test_route()
    assert result == "response"

def test_monocle_trace_http_route_sync():
    @monocle_trace_http_route
    def test_route():
        return "response"

    result = test_route()
    assert result == "response"

def test_propagate_trace_id_from_traceparent():
    with patch('monocle_apptrace.instrumentation.common.instrumentor.propagate_trace_id') as mock_propagate:
        propagate_trace_id_from_traceparent()
        mock_propagate.assert_called_once_with(use_trace_context=True)

import os
import pytest
from unittest.mock import MagicMock, patch
from importlib.metadata import PackageNotFoundError
from opentelemetry.sdk.trace import Span
from opentelemetry.trace import SpanContext, TraceFlags
from monocle_apptrace.instrumentation.common.span_handler import SpanHandler
from monocle_apptrace.instrumentation.common.constants import QUERY

@pytest.fixture
def span_handler():
    return SpanHandler()

@pytest.fixture
def mock_span():
    span = MagicMock(spec=Span)
    span.parent = None
    span.resource = MagicMock()
    span.resource.attributes = {}
    return span

def test_set_instrumentor(span_handler):
    instrumentor = MagicMock()
    span_handler.set_instrumentor(instrumentor)
    assert span_handler.instrumentor == instrumentor

def test_validate(span_handler):
    span_handler.validate(None, None, None, None, None)

def test_pre_tracing(span_handler):
    span_handler.pre_tracing(None, None, None, None, None)

def test_post_tracing(span_handler):
    span_handler.post_tracing(None, None, None, None, None, None)

def test_skip_span(span_handler):
    assert span_handler.skip_span(None, None, None, None, None) == False

def test_pre_task_processing_root_span_with_version(span_handler, mock_span):
    with patch('monocle_apptrace.instrumentation.common.span_handler.version') as mock_version:
        mock_version.return_value = '1.0.0'
        to_wrap = {'package': 'test'}
        span_handler.pre_task_processing(to_wrap, None, None, [], {}, mock_span)
        mock_span.set_attribute.assert_called_with('monocle_apptrace.version', '1.0.0')

def test_pre_task_processing_root_span_version_error(span_handler, mock_span):
    with patch('monocle_apptrace.instrumentation.common.span_handler.version') as mock_version:
        mock_version.side_effect = PackageNotFoundError()
        to_wrap = {'package': 'test'}
        span_handler.pre_task_processing(to_wrap, None, None, [], {}, mock_span)
        mock_span.set_attribute.assert_not_called()

def test_pre_task_processing_pipeline(span_handler, mock_span):
    to_wrap = {'package': 'pipeline'}
    args = [{'prompt_builder': {'question': 'test question'}}]
    with patch('monocle_apptrace.instrumentation.common.span_handler.set_attribute') as mock_set_attr:
        span_handler.pre_task_processing(to_wrap, None, None, args, {}, mock_span)
        mock_set_attr.assert_called_with(QUERY, 'test question')

def test_hydrate_span(span_handler, mock_span):
    with patch.object(span_handler, 'hydrate_attributes') as mock_hydrate_attrs:
        with patch.object(span_handler, 'hydrate_events') as mock_hydrate_events:
            span_handler.hydrate_span({}, None, None, None, {}, None, mock_span)
            mock_hydrate_attrs.assert_called_once()
            mock_hydrate_events.assert_called_once()

def test_hydrate_attributes_with_output_processor(span_handler, mock_span):
    to_wrap = {
        'output_processor': {
            'type': 'test_type',
            'attributes': [[
                {'attribute': 'test_attr', 'accessor': lambda x: 'test_value'}
            ]]
        }
    }
    with patch('monocle_apptrace.instrumentation.common.span_handler.get_scopes', return_value={}):
        span_handler.hydrate_attributes(to_wrap, None, None, None, {}, None, mock_span)
        mock_span.set_attribute.assert_any_call('span.type', 'test_type')
        mock_span.set_attribute.assert_any_call('entity.2.test_attr', 'test_value')
        mock_span.set_attribute.assert_any_call('entity.count', 2)

def test_hydrate_attributes_with_invalid_accessor(span_handler, mock_span):
    def raise_exception():
        raise Exception("Test exception")

    to_wrap = {
        'output_processor': {
            'type': 'test_type',
            'attributes': [[
                {'attribute': 'test_attr', 'accessor': lambda x: raise_exception()}
            ]]
        }
    }
    with patch('monocle_apptrace.instrumentation.common.span_handler.get_scopes', return_value={}):
        span_handler.hydrate_attributes(to_wrap, None, None, None, {}, None, mock_span)
        mock_span.set_attribute.assert_any_call('span.type', 'test_type')
        mock_span.set_attribute.assert_any_call('entity.count', 2)

def test_hydrate_events(span_handler, mock_span):
    to_wrap = {
        'output_processor': {
            'events': [{
                'name': 'test_event',
                'attributes': [
                    {'attribute': 'test_attr', 'accessor': lambda x: 'test_value'}
                ]
            }]
        }
    }
    span_handler.hydrate_events(to_wrap, None, None, None, {}, None, mock_span)
    mock_span.add_event.assert_called_with(
        name='test_event',
        attributes={'test_attr': 'test_value'}
    )

def test_hydrate_events_with_error(span_handler, mock_span):
    def raise_exception():
        raise Exception("Test exception")

    to_wrap = {
        'output_processor': {
            'events': [{
                'name': 'test_event',
                'attributes': [
                    {'attribute': 'test_attr', 'accessor': lambda x: raise_exception()}
                ]
            }]
        }
    }
    span_handler.hydrate_events(to_wrap, None, None, None, {}, None, mock_span)
    mock_span.add_event.assert_called_with(
        name='test_event',
        attributes={}
    )

def test_set_workflow_attributes_with_name(span_handler, mock_span):
    to_wrap = {'package': 'langchain.test'}
    with patch.object(span_handler, 'get_workflow_name', return_value='test_workflow'):
        span_index = span_handler.set_workflow_attributes(to_wrap, mock_span, 1)
        assert span_index == 1
        mock_span.set_attribute.assert_any_call('span.type', 'workflow')
        mock_span.set_attribute.assert_any_call('entity.1.name', 'test_workflow')
        mock_span.set_attribute.assert_any_call('entity.1.type', 'workflow.langchain')

def test_set_workflow_attributes_without_name(span_handler, mock_span):
    to_wrap = {'package': 'unknown'}
    with patch.object(span_handler, 'get_workflow_name', return_value=None):
        span_index = span_handler.set_workflow_attributes(to_wrap, mock_span, 1)
        assert span_index == 1
        mock_span.set_attribute.assert_any_call('entity.1.type', 'workflow.generic')

def test_set_app_hosting_identifier_attribute(span_handler, mock_span, monkeypatch):
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME', 'test-lambda')
    with patch('monocle_apptrace.instrumentation.common.span_handler.service_type_map',
              {'AWS_LAMBDA_FUNCTION_NAME': 'aws'}):
        with patch('monocle_apptrace.instrumentation.common.span_handler.service_name_map',
                  {'aws': 'AWS_LAMBDA_FUNCTION_NAME'}):
            span_index = span_handler.set_app_hosting_identifier_attribute(mock_span, 1)
            assert span_index == 1
            mock_span.set_attribute.assert_any_call('entity.1.type', 'app_hosting.aws')
            mock_span.set_attribute.assert_any_call('entity.1.name', 'test-lambda')

def test_get_workflow_name_from_context(span_handler, mock_span):
    with patch('monocle_apptrace.instrumentation.common.span_handler.get_value', return_value='test_workflow'):
        workflow_name = span_handler.get_workflow_name(mock_span)
        assert workflow_name == 'test_workflow'

def test_get_workflow_name_from_resource(span_handler, mock_span):
    mock_span.resource.attributes = {'service.name': 'test_service'}
    with patch('monocle_apptrace.instrumentation.common.span_handler.get_value', return_value=None):
        workflow_name = span_handler.get_workflow_name(mock_span)
        assert workflow_name == 'test_service'

def test_get_workflow_name_error(span_handler, mock_span):
    with patch('monocle_apptrace.instrumentation.common.span_handler.get_value', side_effect=Exception):
        workflow_name = span_handler.get_workflow_name(mock_span)
        assert workflow_name is None

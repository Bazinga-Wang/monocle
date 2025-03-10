import pytest
from unittest.mock import MagicMock
from monocle_apptrace.instrumentation.metamodel.requests._helper import (
    request_pre_task_processor,
    request_skip_span,
    RequestSpanHandler
)

def test_request_pre_task_processor_no_headers():
    kwargs = {}
    request_pre_task_processor(kwargs)
    assert 'headers' in kwargs
    assert isinstance(kwargs['headers'], dict)

def test_request_pre_task_processor_existing_headers():
    original_headers = {'Content-Type': 'application/json'}
    kwargs = {'headers': original_headers.copy()}
    request_pre_task_processor(kwargs)
    assert 'headers' in kwargs
    assert isinstance(kwargs['headers'], dict)
    assert 'Content-Type' in kwargs['headers']
    assert kwargs['headers']['Content-Type'] == 'application/json'

def test_request_pre_task_processor_empty_headers():
    kwargs = {'headers': {}}
    request_pre_task_processor(kwargs)
    assert 'headers' in kwargs
    assert isinstance(kwargs['headers'], dict)

def test_request_skip_span_no_url():
    kwargs = {}
    assert request_skip_span(kwargs) is True

def test_request_skip_span_empty_url():
    kwargs = {'url': ''}
    assert request_skip_span(kwargs) is True

def test_request_skip_span_allowed_url(monkeypatch):
    monkeypatch.setattr('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls',
                        ['http://allowed.com'])
    kwargs = {'url': 'http://allowed.com/path'}
    assert request_skip_span(kwargs) is False

def test_request_skip_span_not_allowed_url(monkeypatch):
    monkeypatch.setattr('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls',
                        ['http://allowed.com'])
    kwargs = {'url': 'http://other.com/path'}
    assert request_skip_span(kwargs) is True

def test_request_skip_span_multiple_allowed_urls(monkeypatch):
    monkeypatch.setattr('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls',
                        ['http://allowed1.com', 'http://allowed2.com'])
    kwargs = {'url': 'http://allowed2.com/path'}
    assert request_skip_span(kwargs) is False

def test_request_skip_span_url_with_whitespace(monkeypatch):
    monkeypatch.setattr('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls',
                        ['  http://allowed.com  '])
    kwargs = {'url': 'http://allowed.com/path'}
    assert request_skip_span(kwargs) is False

def test_request_span_handler_pre_task_processing():
    handler = RequestSpanHandler()
    kwargs = {}
    to_wrap = MagicMock()
    wrapped = MagicMock()
    instance = MagicMock()
    args = ()
    span = MagicMock()

    handler.pre_task_processing(to_wrap, wrapped, instance, args, kwargs, span)
    assert 'headers' in kwargs
    assert isinstance(kwargs['headers'], dict)

def test_request_span_handler_skip_span_no_url():
    handler = RequestSpanHandler()
    kwargs = {}
    to_wrap = MagicMock()
    wrapped = MagicMock()
    instance = MagicMock()
    args = ()

    assert handler.skip_span(to_wrap, wrapped, instance, args, kwargs) is True

def test_request_span_handler_skip_span_allowed_url(monkeypatch):
    monkeypatch.setattr('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls',
                        ['http://allowed.com'])
    handler = RequestSpanHandler()
    kwargs = {'url': 'http://allowed.com/path'}
    to_wrap = MagicMock()
    wrapped = MagicMock()
    instance = MagicMock()
    args = ()

    assert handler.skip_span(to_wrap, wrapped, instance, args, kwargs) is False

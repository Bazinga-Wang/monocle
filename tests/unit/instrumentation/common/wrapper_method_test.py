import pytest
from monocle_apptrace.instrumentation.common.wrapper_method import WrapperMethod
from monocle_apptrace.instrumentation.common.span_handler import SpanHandler
from monocle_apptrace.instrumentation.metamodel.botocore.handlers.botocore_span_handler import BotoCoreSpanHandler
from monocle_apptrace.instrumentation.metamodel.flask._helper import FlaskSpanHandler
from monocle_apptrace.instrumentation.metamodel.requests._helper import RequestSpanHandler
from monocle_apptrace.instrumentation.common.wrapper import task_wrapper, scope_wrapper
from monocle_apptrace.instrumentation.common.wrapper_method import MONOCLE_SPAN_HANDLERS

def test_wrapper_method_to_dict_with_task_wrapper():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_name="test_span",
        output_processor="test_processor",
        wrapper_method=task_wrapper,
        span_handler="default"
    )

    result = wrapper.to_dict()

    assert result["package"] == "test_package"
    assert result["object"] == "test_object"
    assert result["method"] == "test_method"
    assert result["span_name"] == "test_span"
    assert result["output_processor"] == "test_processor"
    assert result["wrapper_method"] == task_wrapper
    assert result["span_handler"] == "default"
    assert result["scope_name"] is None

def test_wrapper_method_to_dict_with_scope_wrapper():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        scope_name="test_scope"
    )

    result = wrapper.to_dict()

    assert result["wrapper_method"] == scope_wrapper
    assert result["scope_name"] == "test_scope"

def test_wrapper_method_get_span_handler_default():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_handler=MONOCLE_SPAN_HANDLERS["default"].__class__
    )

    handler = wrapper.get_span_handler()
    assert isinstance(handler, SpanHandler)

def test_wrapper_method_get_span_handler_botocore():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_handler=MONOCLE_SPAN_HANDLERS["botocore_handler"].__class__
    )

    handler = wrapper.get_span_handler()
    assert isinstance(handler, BotoCoreSpanHandler)

def test_wrapper_method_get_span_handler_flask():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_handler=MONOCLE_SPAN_HANDLERS["flask_handler"].__class__
    )

    handler = wrapper.get_span_handler()
    assert isinstance(handler, FlaskSpanHandler)

def test_wrapper_method_get_span_handler_request():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_handler=MONOCLE_SPAN_HANDLERS["request_handler"].__class__
    )

    handler = wrapper.get_span_handler()
    assert isinstance(handler, RequestSpanHandler)

def test_wrapper_method_to_dict_minimal():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method"
    )

    result = wrapper.to_dict()

    assert result["package"] == "test_package"
    assert result["object"] == "test_object"
    assert result["method"] == "test_method"
    assert result["span_name"] is None
    assert result["output_processor"] is None
    assert result["wrapper_method"] == task_wrapper
    assert result["scope_name"] is None

def test_wrapper_method_to_dict_all_fields():
    wrapper = WrapperMethod(
        package="test_package",
        object_name="test_object",
        method="test_method",
        span_name="test_span",
        output_processor="test_processor",
        wrapper_method=task_wrapper,
        span_handler=MONOCLE_SPAN_HANDLERS["default"].__class__,
        scope_name="test_scope"
    )

    result = wrapper.to_dict()

    assert result["package"] == "test_package"
    assert result["object"] == "test_object"
    assert result["method"] == "test_method"
    assert result["span_name"] == "test_span"
    assert result["output_processor"] == "test_processor"
    assert result["wrapper_method"] == scope_wrapper
    assert result["span_handler"] == MONOCLE_SPAN_HANDLERS["default"].__class__
    assert result["scope_name"] == "test_scope"

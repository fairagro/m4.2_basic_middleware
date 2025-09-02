"""
defines a decorator function that creates an OTEL span with an appropiate name
"""

import functools
import inspect
from opentelemetry import trace

def traced(func):
    """
    a decorator function that creates an OTEL span with an appropiate name
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        span_name = _get_span_name(func, args)
        tracer = trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(span_name):
            return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        span_name = _get_span_name(func, args)
        tracer = trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(span_name):
            return func(*args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def _get_span_name(func, args):
    """
    creates a OTEL span name for a function
    """
    cls_name = ""
    if args:
        first = args[0]
        # Instance method
        if hasattr(first, "__class__") and func.__name__ in first.__class__.__dict__:
            cls_name = first.__class__.__name__ + "."
        # Classmethod
        elif inspect.isclass(first) and func.__name__ in first.__dict__:
            cls_name = first.__name__ + "."
    return cls_name + func.__name__

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
        tracer = trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(func.__qualname__):
            return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tracer = trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(func.__qualname__):
            return func(*args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


import json
import logging

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from backend.app.telemetry import JsonLogFormatter


def test_json_log_formatter_includes_active_trace_and_span_ids():
    span_context = SpanContext(
        trace_id=0x1234567890ABCDEF1234567890ABCDEF,
        span_id=0x1234567890ABCDEF,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )

    with trace.use_span(NonRecordingSpan(span_context)):
        formatted = JsonLogFormatter().format(record)

    entry = json.loads(formatted)
    assert entry["trace_id"] == "1234567890abcdef1234567890abcdef"
    assert entry["span_id"] == "1234567890abcdef"

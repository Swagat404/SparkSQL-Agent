"""
Tracing utilities for Spark PostgreSQL Agent.
"""

from spark_pg_agent_formal.tracing.tracer import (
    trace_manager,
    trace_llm_call,
    trace_compilation_phase,
    trace_code_execution,
    enable_console_output,
    disable_console_output
)

__all__ = [
    "trace_manager",
    "trace_llm_call", 
    "trace_compilation_phase",
    "trace_code_execution",
    "enable_console_output",
    "disable_console_output"
] 
"""
Tracing utilities for Spark PostgreSQL Agent.

This module provides decorators and utilities for tracing execution and compilation phases.
"""
import io
import os
import sys
import time
import uuid
from functools import wraps
from typing import Callable, List, Dict, Any, Optional

from agenttrace import TraceManager

# Environment checks for tracing behavior
QUIET_TRACING = True #os.environ.get("SPARK_PG_AGENT_QUIET_TRACING") == "1"
NO_SPINNER = os.environ.get("SPARK_PG_AGENT_NO_SPINNER") == "1" or os.environ.get("AGENTTRACE_NO_SPINNER") == "1"

# Enable console output by default, unless quiet mode is enabled
ENABLE_CONSOLE_OUTPUT = not QUIET_TRACING

# Create a log file for tracing instead of using stdout when in interactive mode
TRACE_LOG_FILE = os.environ.get("SPARK_PG_AGENT_TRACE_LOG", None)
trace_log_stream = None

if TRACE_LOG_FILE:
    try:
        trace_log_stream = open(TRACE_LOG_FILE, 'a')
    except:
        # Fall back to console if file can't be opened
        pass

# Create a singleton instance of TraceManager with appropriate options
trace_manager = TraceManager(
    db_path="/Users/swagatbhowmik/CS projects/TensorStack/Github version/SparkSQL-Agent/spark_pg_agent_traces.db", 
    colored_logging=ENABLE_CONSOLE_OUTPUT  # Use colored_logging instead of console_output_enabled
)

def trace_print(*args, **kwargs):
    """
    Print function that writes to the trace log file if available,
    otherwise to stdout but only if console output is enabled.
    """
    if trace_log_stream:
        print(*args, file=trace_log_stream, **kwargs)
        trace_log_stream.flush()
    elif ENABLE_CONSOLE_OUTPUT:
        # Only print to console if explicitly enabled
        print(*args, **kwargs)


class NullIO(io.IOBase):
    """A null IO class that discards all writes."""
    def write(self, *args, **kwargs):
        return 0
    
    def writelines(self, *args, **kwargs):
        return
    
    def flush(self, *args, **kwargs):
        return


def disable_console_output():
    """Disable console output from tracing."""
    global ENABLE_CONSOLE_OUTPUT
    ENABLE_CONSOLE_OUTPUT = False


def enable_console_output():
    """Enable console output from tracing."""
    global ENABLE_CONSOLE_OUTPUT
    ENABLE_CONSOLE_OUTPUT = True


def redirect_outputs():
    """
    Redirect both stdout and stderr to null streams.
    
    Returns:
        tuple: Original stdout and stderr
    """
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = NullIO()
    sys.stderr = NullIO()
    return original_stdout, original_stderr


def restore_outputs(original_stdout, original_stderr):
    """
    Restore stdout and stderr to their original values.
    
    Args:
        original_stdout: Original stdout stream
        original_stderr: Original stderr stream
    """
    sys.stdout = original_stdout
    sys.stderr = original_stderr


def trace_llm_call(func: Callable) -> Callable:
    """
    Decorator to trace LLM calls.
    
    Args:
        func: The function to trace (typically get_completion)
        
    Returns:
        Wrapped function that traces LLM calls
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # The first arg after self is usually the prompt
        prompt = args[1] if len(args) > 1 else kwargs.get('prompt', 'Unknown prompt')
        
        # Get provider type from the instance
        provider_type = args[0].__class__.__name__ if args else "UnknownProvider"
        
        # Generate a unique session ID for this call
        session_id = f"llm_call_{uuid.uuid4().hex[:8]}"
        
        # Look for a compilation session ID in the prompt
        # This is used to group all traces from the same compilation session
        compilation_session_id = None
        transformation_id = None
        attempt_number = None
        
        if isinstance(prompt, str):
            # Extract session ID from prompt if it's there
            import re
            session_match = re.search(r'session_id:([a-zA-Z0-9_-]+)', prompt)
            if session_match:
                compilation_session_id = session_match.group(1)
                
            # Extract transformation_id from prompt if available
            transform_match = re.search(r'transformation_id:([a-zA-Z0-9_-]+)', prompt)
            if transform_match:
                transformation_id = transform_match.group(1)
                
            # Extract attempt_number from prompt if available
            attempt_match = re.search(r'attempt_number:(\d+)', prompt)
            if attempt_match:
                attempt_number = int(attempt_match.group(1))
        
        # Use the compilation session ID if found, otherwise use the generated one
        trace_session_id = compilation_session_id or session_id
        
        # Redirect outputs if console output is disabled
        original_stdout, original_stderr = None, None
        if not ENABLE_CONSOLE_OUTPUT:
            original_stdout, original_stderr = redirect_outputs()
        
        # Build tags list with transformation info when available
        tags = ["llm", provider_type]
        if transformation_id:
            tags.append(f"transform-{transformation_id}")
        if attempt_number:
            tags.append(f"attempt-{attempt_number}")
            
        # Define the traced function that will be decorated by tracer.trace
        @trace_manager.trace(tags=tags, session_id=trace_session_id)
        def traced_llm_call():
            # Measure time and call the function
            start_time = time.time()
            try:
                # For LLM calls, we suppress inline progress printing to avoid command-line interference
                trace_print(f"[TRACE] LLM call to {provider_type} in progress...")
                
                response = func(*args, **kwargs)
                end_time = time.time()
                
                trace_print(f"[TRACE] LLM call completed in {end_time - start_time:.2f}s")
                
                # Store attributes as a return value dictionary that AgentTrace can capture
                trace_data = {
                    "prompt": prompt,
                    "response": response,
                    "duration": end_time - start_time,
                    "provider": provider_type
                }
                
                # Add transformation tracking info
                if transformation_id:
                    trace_data["transformation_id"] = transformation_id
                if attempt_number:
                    trace_data["attempt_number"] = attempt_number
                    
                return trace_data
            except Exception as e:
                error_data = {
                    "prompt": prompt,
                    "error": str(e),
                    "provider": provider_type
                }
                
                # Add transformation tracking info to error data too
                if transformation_id:
                    error_data["transformation_id"] = transformation_id
                if attempt_number:
                    error_data["attempt_number"] = attempt_number
                    
                return error_data
        
        try:
            # Call the traced function
            result = traced_llm_call()
        finally:
            # Restore outputs if we redirected them
            if original_stdout is not None and original_stderr is not None:
                restore_outputs(original_stdout, original_stderr)
        
        # If there was an error in the result, raise it
        if "error" in result:
            raise Exception(result["error"])
        
        # Return the actual response
        return result["response"]
    
    return wrapper


def trace_compilation_phase(phase: str) -> Callable:
    """
    Decorator to trace a compilation phase.
    
    Args:
        phase: Name of the compilation phase
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the compilation context if it's in the arguments
            context = None
            # Try to find context in the arguments
            for arg in args:
                if hasattr(arg, 'user_request') and hasattr(arg, 'compilation_session_id'):
                    context = arg
                    break
            
            # Check context in kwargs
            if context is None and 'context' in kwargs:
                context = kwargs['context']
                
            # Extract request info and session ID from context or use defaults
            user_request = "Unknown request"
            session_id = f"compile_{uuid.uuid4().hex[:8]}"
            transformation_id = None
            attempt_number = None
            
            if context:
                # Use context information when available
                if hasattr(context, 'user_request'):
                    user_request = context.user_request
                if hasattr(context, 'compilation_session_id'):
                    session_id = context.compilation_session_id
                if hasattr(context, 'transformation_id'):
                    transformation_id = context.transformation_id
                if hasattr(context, 'attempt_number'):
                    attempt_number = context.attempt_number
            
            # Redirect outputs if console output is disabled
            original_stdout, original_stderr = None, None
            if not ENABLE_CONSOLE_OUTPUT:
                original_stdout, original_stderr = redirect_outputs()
                
            # Flag to track if this is the start or end of a phase
            is_start = kwargs.pop('is_start', False) if 'is_start' in kwargs else False
            
            # Create tags for the trace
            tags = ["compiler", phase.lower().replace(" ", "_")]
            if transformation_id:
                tags.append(f"transform-{transformation_id}")
            if attempt_number:
                tags.append(f"attempt-{attempt_number}")
                
            # Log start of phase using trace_print
            phase_state = "START" if is_start else "END"
            trace_print(f"[TRACE] Compilation phase: {phase} - {phase_state} (session: {session_id})")
            
            @trace_manager.trace(tags=tags, session_id=session_id)
            def traced_phase():
                try:
                    # Execute the phase
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log completion with trace_print
                    trace_print(f"[TRACE] Compilation phase {phase} completed in {execution_time:.2f}s (session: {session_id})")
                    
                    # Prepare result data
                    phase_data = {
                        "user_request": user_request,
                        "phase": phase,
                        "state": phase_state,
                        "execution_time_seconds": execution_time
                    }
                    
                    # Add transformation tracking info 
                    if transformation_id:
                        phase_data["transformation_id"] = transformation_id
                    if attempt_number:
                        phase_data["attempt_number"] = attempt_number
                    
                    return phase_data, result
                except Exception as e:
                    error_data = {
                        "user_request": user_request,
                        "phase": phase,
                        "state": phase_state,
                        "error": str(e)
                    }
                    
                    # Add transformation tracking info to error data too
                    if transformation_id:
                        error_data["transformation_id"] = transformation_id
                    if attempt_number:
                        error_data["attempt_number"] = attempt_number
                        
                    return error_data, None
            
            try:
                # Call the traced function
                data, result = traced_phase()
                
                # If there was an error in the data, raise it
                if "error" in data:
                    raise Exception(data["error"])
                    
                return result
            finally:
                # Restore outputs if we redirected them
                if original_stdout is not None and original_stderr is not None:
                    restore_outputs(original_stdout, original_stderr)
        
        return wrapper
    
    return decorator


def trace_code_execution(func: Callable) -> Callable:
    """
    Decorator to trace code execution.
    
    Args:
        func: The function to trace (typically execute)
        
    Returns:
        Wrapped function that traces code execution
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we have a context object with compilation session ID
        context = None
        transformation_id = None
        attempt_number = None
        
        # Generate a unique session ID for this execution
        session_id = f"exec_{uuid.uuid4().hex[:8]}"
        user_request = "Unknown request"
        
        # Look for context, transformation_id, and attempt_number in args/kwargs
        # First check if code is passed as a keyword argument
        code = kwargs.get('code', None)
        
        # Try to find context in args
        for arg in args:
            # Different context objects might have different attributes
            if hasattr(arg, 'user_request'):
                user_request = arg.user_request
                context = arg
                
            if hasattr(arg, 'compilation_session_id'):
                session_id = arg.compilation_session_id
                
            if hasattr(arg, 'transformation_id'):
                transformation_id = arg.transformation_id
                
            if hasattr(arg, 'attempt_number'):
                attempt_number = arg.attempt_number
        
        # Create tags for the trace
        tags = ["execution"]
        if transformation_id:
            tags.append(f"transform-{transformation_id}")
        if attempt_number:
            tags.append(f"attempt-{attempt_number}")
        
        # Log start of execution using trace_print
        trace_print(f"[TRACE] Code execution started (session: {session_id})")
            
        @trace_manager.trace(tags=tags, session_id=session_id)
        def traced_execution():
            try:
                # Execute the function
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log completion with trace_print
                trace_print(f"[TRACE] Code execution completed in {execution_time:.2f}s (session: {session_id})")
                
                # Build the execution data
                execution_data = {
                    "user_request": user_request,
                    "execution_time_seconds": execution_time,
                    "successful": True
                }
                
                # Add transformation tracking info
                if transformation_id:
                    execution_data["transformation_id"] = transformation_id
                if attempt_number:
                    execution_data["attempt_number"] = attempt_number
                
                # Add code if available
                if code:
                    execution_data["code"] = code
                    
                # Add SQL if available
                if context and hasattr(context, "sql"):
                    execution_data["sql"] = context.sql
                    
                return execution_data, result
            except Exception as e:
                error_data = {
                    "user_request": user_request,
                    "error": str(e),
                    "successful": False
                }
                
                # Add transformation tracking info to error data too
                if transformation_id:
                    error_data["transformation_id"] = transformation_id
                if attempt_number:
                    error_data["attempt_number"] = attempt_number
                    
                # Add code if available
                if code:
                    error_data["code"] = code
                    
                return error_data, None
                
        # Execute the traced function
        data, result = traced_execution()
        
        # Return the result, whether successful or not
        return result
    
    return wrapper 
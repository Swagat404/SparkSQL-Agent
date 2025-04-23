"""
Main agent implementation for Spark PostgreSQL Agent.

This module provides the core TransformationAgent class that orchestrates
the entire process of transforming natural language requests into executable code.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
import traceback
from datetime import datetime
import logging

from pyspark.sql import SparkSession

from spark_pg_agent_formal.core.types import AgentConfig, AgentState, CompilationPhase
from spark_pg_agent_formal.core.memory import AgentMemory
from spark_pg_agent_formal.db.schema_memory import SchemaMemory
from spark_pg_agent_formal.db.db_manager import DatabaseManager
from spark_pg_agent_formal.llm.compiler import MultiPhaseLLMCompiler, CompilationContext
from spark_pg_agent_formal.llm.providers import get_provider, LLMProvider
from spark_pg_agent_formal.execution.executor import SparkExecutor
from spark_pg_agent_formal.execution.validator import ResultValidator, ValidationResult
from spark_pg_agent_formal.execution.executor import ExecutionResult

# Import phase_tracker safely to avoid circular imports
try:
    from spark_pg_agent_formal.phase_tracker import phase_tracker
except ImportError:
    # Create a dummy phase tracker for safety
    class DummyTracker:
        def _handle_trace_event(self, *args, **kwargs):
            pass
    phase_tracker = DummyTracker()


class TransformationAgent:
    """
    Main agent class for handling transformation requests.
    
    This class orchestrates the full transformation workflow from request to execution.
    """
    
    def __init__(self, postgres_config: Dict[str, Any], config: Optional[AgentConfig] = None):
        """
        Initialize the transformation agent.
        
        Args:
            postgres_config: PostgreSQL connection configuration
            config: Optional agent configuration
        """
        # Store configuration
        self.postgres_config = postgres_config
        self.config = config or AgentConfig()
        
        # Create memory systems
        self.memory = AgentMemory()
        self.schema_memory = SchemaMemory()
        
        # Set up database manager
        self.db_manager = DatabaseManager(postgres_config)
        
        # Set up LLM provider
        self.llm_provider = get_provider(self.config.llm_provider)
        
        # Set up compiler
        self.compiler = MultiPhaseLLMCompiler(self.llm_provider, self.schema_memory)
        
        # Set up executor
        self.executor = SparkExecutor(postgres_config)
        
        # Set up validator
        self.validator = ResultValidator()
        
        # Initialize database schema
        self._initialize_schema()
        
        # Context tracking for relative requests
        self._last_request = None
        self._last_code = None
        self._last_result = None
        self._transformation_history = []
    
    def process_request(self, request: str) -> ExecutionResult:
        """
        Process a transformation request from the user.
        
        This method handles the end-to-end process from request to execution.
        
        Args:
            request: User's natural language transformation request
            
        Returns:
            ExecutionResult object containing the result or error information
        """
        max_attempts = self.config.max_attempts if hasattr(self.config, 'max_attempts') else 3
        attempt = 1
        last_error = None
        previous_errors = []
        
        # Check if this is a refinement of a previous rejected transformation
        is_refinement = self.memory.is_refinement_active()
        if is_refinement:
            print("Processing as refinement of previously rejected transformation")
            
        while attempt <= max_attempts:
            try:
                # Log the request in memory
                self.memory.add_to_conversation("user", request)
                
                # Check if this is a relative request
                is_relative_request = self._is_relative_request(request)
                if is_relative_request and not is_refinement:
                    print(f"Detected relative request referring to previous: '{self._last_request}'")
                
                # Process the transformation
                result = self._process_transformation(request, is_relative_request, previous_errors, is_refinement)
                
                # If successful, store the context for future requests
                if result.success:
                    # Store results in agent properties
                    self._last_request = request
                    self._last_code = result.code
                    self._last_result = result
                    
                    # Add to transformation history
                    self._transformation_history.append({
                        "request": request,
                        "code": result.code,  # Store the code for future reference
                        "timestamp": datetime.now().isoformat(),
                        "success": result.success
                    })
                    
                    # Keep only the last 5 transformations in history
                    if len(self._transformation_history) > 5:
                        self._transformation_history = self._transformation_history[-5:]
                        
                    # Also log the result in memory
                    self.memory.add_to_conversation(
                        "system", 
                        f"Transformation executed successfully with {result.result_data.count() if hasattr(result.result_data, 'count') else 'N/A'} results"
                    )
                    
                    # Clear refinement context since we succeeded
                    if is_refinement:
                        self.memory.clear_refinement_context()
                        
                    return result
                else:
                    # Log error in memory
                    error_msg = f"Attempt {attempt}/{max_attempts} failed: {result.error}"
                    self.memory.add_to_conversation("system", error_msg)
                    print(error_msg)
                    
                    # Store the last error
                    last_error = result.error
                    previous_errors.append({
                        "attempt": attempt,
                        "error": result.error,
                        "code": result.code
                    })
                    
                    # If this was the last attempt, return the failed result
                    if attempt == max_attempts:
                        return result
                    
                    # Otherwise, try again
                    attempt += 1
                    continue
                
            except Exception as e:
                traceback.print_exc()
                error_message = f"Error processing request (attempt {attempt}/{max_attempts}): {str(e)}"
                
                # Log error in memory
                self.memory.add_to_conversation("system", error_message)
                previous_errors.append({
                    "attempt": attempt,
                    "error": str(e),
                    "code": None
                })
                
                # If this was the last attempt, return an error result
                if attempt == max_attempts:
                    return ExecutionResult(
                        success=False,
                        error=error_message,
                        transformation_id=str(uuid.uuid4())
                    )
                
                # Otherwise, try again
                attempt += 1
        
        # If we get here, all attempts failed
        return ExecutionResult(
            success=False,
            error=f"All {max_attempts} attempts failed. Last error: {last_error}",
            transformation_id=str(uuid.uuid4())
        )
    
    def _is_relative_request(self, request: str) -> bool:
        """
        Determine if a request is relative to previous results.
        
        Args:
            request: The user's request
            
        Returns:
            True if the request appears to be relative, False otherwise
        """
        if not self.memory.previous_transformations:
            return False
            
        # Use the memory's find_related_transformation to detect relative requests
        related_transformation = self.memory.find_related_transformation(request)
        
        # Consider request relative if any relation is found
        return related_transformation is not None
    
    def _process_transformation(self, request: str, is_relative: bool = False, previous_errors=None, is_refinement=False) -> ExecutionResult:
        """
        Process a transformation request.
        
        Args:
            request: User's transformation request
            is_relative: Whether this request is relative to previous results
            previous_errors: List of errors from previous attempts
            is_refinement: Whether this request is a refinement of a previous rejected transformation
            
        Returns:
            ExecutionResult containing the results or error information
        """
        # Generate a transformation ID
        transformation_id = str(uuid.uuid4())
        
        # Get PostgreSQL connection details
        postgres_config = self.postgres_config
        
        # Initialize compilation context
        context = CompilationContext(
            user_request=request,
            schema_memory=self.schema_memory,
            postgres_config=postgres_config,
            transformation_id=transformation_id
        )
        
        # If we have previous errors, add them to the context
        if previous_errors:
            # Use the serializer to handle date objects
            context.phase_results["previous_errors"] = self._serialize_for_prompt(previous_errors)
            print(f"Including {len(previous_errors)} previous errors in compilation context")
        
        # Get memory context for the current request
        memory_context = self.memory.get_relevant_context(request)
        
        # If this is a refinement, add the rejected transformation's context
        if is_refinement:
            ref_context = self.memory.refinement_context
            context.phase_results["refinement_context"] = {
                "original_request": ref_context["original_request"],
                "original_code": ref_context["original_code"]
            }
            
            # Also add original result summary if available
            if ref_context["original_result"] and hasattr(ref_context["original_result"], 'result_data'):
                result_summary = self._summarize_result(ref_context["original_result"])
                context.phase_results["original_result_summary"] = self._serialize_for_prompt(result_summary)
                
            print(f"Added refinement context from rejected transformation: '{ref_context['original_request']}'")
        
        # Handle references to previous transformations
        else:
            # Find related transformation context from memory
            related_transformation = self.memory.find_related_transformation(request)
            
            if related_transformation:
                reference_type = related_transformation.get("type", "")
                base_transformation = related_transformation.get("base_transformation", {})
                print(f"Found {reference_type} to previous transformation: '{base_transformation.get('request', '')}'")
                
                # Add relevant context based on the type of reference
                if reference_type == "explicit_reference":
                    # User explicitly referenced a specific transformation (e.g., "go back to first query")
                    print(f"Processing explicit reference to step {base_transformation.get('step_number', '')}")
                    context.phase_results["referenced_transformation"] = self._serialize_for_prompt(base_transformation)
                    context.phase_results["reference_type"] = related_transformation.get("reference_type", "")
                    
                    # Set the previous request/code for the compiler context
                    context.phase_results["previous_request"] = base_transformation.get("request", "")
                    context.phase_results["previous_code"] = base_transformation.get("code", "")
                    
                elif reference_type == "relative_reference":
                    # User made a relative reference like "show me the same but only for US"
                    print(f"Processing relative reference to most recent transformation")
                    context.phase_results["previous_request"] = base_transformation.get("request", "")
                    context.phase_results["previous_code"] = base_transformation.get("code", "")
                    
                elif reference_type == "entity_reference":
                    # User referenced entities from a previous transformation
                    entity = related_transformation.get("reference_type", "").replace("entity_", "")
                    print(f"Processing entity reference to '{entity}' from a previous transformation")
                    context.phase_results["previous_request"] = base_transformation.get("request", "")
                    context.phase_results["previous_code"] = base_transformation.get("code", "")
                    context.phase_results["referenced_entity"] = entity
                
                # Always include the base transformation's result summary if available
                result_summary = base_transformation.get("result_summary", {})
                if result_summary:
                    context.phase_results["previous_result_summary"] = self._serialize_for_prompt(result_summary)
            
            # Add memory context with implied intentions, focus entities, etc.
            context.phase_results["memory_context"] = self._serialize_for_prompt(memory_context)
            
            # Print useful debug info
            if "filter_requested" in memory_context:
                print(f"Detected filter request in context: {memory_context.get('potential_filter_value', 'unknown value')}")
            
            if "implied_intentions" in memory_context and memory_context["implied_intentions"]:
                print(f"Detected implied intentions: {', '.join(memory_context['implied_intentions'])}")
        
        try:
            # Compile the request to PySpark code
            print("Compiling request...")
            code = self.compiler.compile_with_context(context)
            
            # Execute the generated code
            print("Executing generated code...")
            
            # Track execution phase start
            if hasattr(context, "compilation_session_id"):
                phase_tracker._handle_trace_event({
                    'session_id': context.compilation_session_id,
                    'tags': ['executing_query', 'phase_start'],
                    'timestamp': time.time()
                })
                
            execution_result = self.executor.execute(code)
            
            # Track execution phase end
            if hasattr(context, "compilation_session_id"):
                if execution_result.success:
                    # Success message
                    execution_content = f"Query executed successfully in {execution_result.execution_time:.3f} seconds."
                    
                    # Add row count if available
                    if hasattr(execution_result.result_data, "count"):
                        try:
                            row_count = execution_result.result_data.count()
                            execution_content += f"\nReturned {row_count} rows."
                        except:
                            pass
                    
                    phase_tracker._handle_trace_event({
                        'session_id': context.compilation_session_id,
                        'tags': ['executing_query', 'phase_end'],
                        'thinking': execution_content,
                        'timestamp': time.time()
                    })
                else:
                    # Error message
                    phase_tracker._handle_trace_event({
                        'session_id': context.compilation_session_id,
                        'tags': ['executing_query', 'phase_end'],
                        'thinking': f"Error: {execution_result.error}",
                        'timestamp': time.time()
                    })
                
            # Validate the execution result
            validation_result = self.validator.validate(execution_result)
            
            # Create the final result
            result = ExecutionResult(
                success=validation_result.valid,
                code=code,
                execution_time=execution_result.execution_time,
                result_data=execution_result.result_data,
                error=validation_result.errors[0] if validation_result.errors else None,
                transformation_id=transformation_id
            )
            
            # Store successful transformation in memory for future relative requests
            if result.success:
                # Extract tables and columns used from the code
                tables_used = self._extract_tables_used(code)
                columns_used = self._extract_columns_used(code)
                
                # Create a result summary
                result_summary = self._summarize_result(result)
                
                # Remember the transformation in memory
                step_number = self.memory.remember_transformation(
                    request=request,
                    code=code,
                    tables_used=tables_used,
                    columns_used=columns_used,
                    result_summary=self._serialize_for_prompt(result_summary)
                )
                
                # Store the current request/code as last for future reference
                self._last_request = request
                self._last_code = code
                self._last_result = result
                
                print(f"Stored transformation as step {step_number} in memory with tables: {tables_used}")
            
            return result
            
        except Exception as e:
            traceback.print_exc()
            return ExecutionResult(
                success=False,
                code=code if 'code' in locals() else None,
                error=f"Error during transformation: {str(e)}",
                transformation_id=transformation_id
            )
    
    def _summarize_result(self, result: ExecutionResult) -> Dict[str, Any]:
        """
        Create a summary of the execution result for memory storage.
        
        Args:
            result: The execution result to summarize
            
        Returns:
            Dictionary with result summary
        """
        summary = {
            "success": result.success,
            "transformation_id": result.transformation_id,
            "execution_time": result.execution_time
        }
        
        # Add data shape information if available
        if hasattr(result, 'result_data') and result.result_data is not None:
            try:
                if hasattr(result.result_data, 'shape'):
                    # For pandas DataFrame
                    summary["row_count"] = result.result_data.shape[0]
                    summary["column_count"] = result.result_data.shape[1]
                    summary["columns"] = list(result.result_data.columns)
                    
                    # Sample a few rows (up to 5) for context
                    if result.result_data.shape[0] > 0:
                        summary["sample_data"] = result.result_data.head(5).to_dict('records')
                elif hasattr(result.result_data, 'count'):
                    # For Spark DataFrame
                    summary["row_count"] = result.result_data.count()
                    summary["column_count"] = len(result.result_data.columns)
                    summary["columns"] = result.result_data.columns
                    
                    # Sample a few rows (up to 5) for context
                    sample_rows = result.result_data.limit(5).collect()
                    summary["sample_data"] = [row.asDict() for row in sample_rows]
            except Exception as e:
                # If summarization fails, include error but continue
                summary["summarization_error"] = str(e)
                
        return summary
    
    def _initialize_schema(self) -> None:
        """Initialize the schema memory from the database"""
        try:
            # Connect to the database
            if not self.db_manager.test_connection():
                if not self.db_manager.connect():
                    print("Failed to connect to the database")
                    return
            
            # Load schema information
            print("Loading database schema...")
            if self.db_manager.load_schema():
                # Get the schema memory
                self.schema_memory = self.db_manager.get_schema_memory()
                
                # Log success
                table_count = len(self.schema_memory.get_all_table_names())
                print(f"Schema loaded successfully. Found {table_count} tables.")
            else:
                print("Failed to load schema information")
        
        except Exception as e:
            print(f"Error initializing schema: {str(e)}")
    
    def confirm_result(self, confirmed: bool) -> None:
        """
        Handle result confirmation from the user.
        
        Args:
            confirmed: Whether the user confirmed the result
        """
        # Log the confirmation
        self.memory.add_to_conversation(
            "system",
            f"User {'confirmed' if confirmed else 'rejected'} the transformation result."
        )
        
        # If the user rejected the result, mark this as a refinement context for the next request
        if not confirmed and self._last_result:
            self.memory.set_refinement_context(self._last_request, self._last_code, self._last_result)
            print("Storing context for refinement in the next request")
            
            # Don't clear last_request/code so they can be referenced in the next query
        elif confirmed:
            # If confirmed, clear the refinement context
            self.memory.clear_refinement_context()
    
    def _serialize_for_prompt(self, obj):
        """
        Serialize an object to JSON, handling special types like dates.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, dict):
            return {k: self._serialize_for_prompt(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_prompt(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # Handle date/datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Handle custom objects
            return self._serialize_for_prompt(obj.__dict__)
        else:
            return obj
    
    def shutdown(self) -> None:
        """Clean up resources"""
        # Shutdown the Spark executor
        if self.executor:
            self.executor.shutdown()
        
        # Disconnect from the database
        if self.db_manager:
            self.db_manager.disconnect()
    
    def _extract_tables_used(self, code: str) -> List[str]:
        """
        Extract table names used in the code.
        
        Args:
            code: PySpark code
            
        Returns:
            List of table names
        """
        # Simple implementation - extract table names from code
        # This is a basic implementation and could be improved
        tables = []
        table_names = self.schema_memory.get_all_table_names()
        
        for table in table_names:
            if f'"{table}"' in code or f"'{table}'" in code:
                tables.append(table)
                
        return tables
        
    def _extract_columns_used(self, code: str) -> Dict[str, List[str]]:
        """
        Extract columns used for each table in the code.
        
        Args:
            code: PySpark code
            
        Returns:
            Dictionary mapping tables to their columns used
        """
        # This is a simple implementation that could be improved
        columns_used = {}
        tables = self._extract_tables_used(code)
        
        for table in tables:
            columns = self.schema_memory.get_table_columns(table)
            columns_used[table] = []
            
            for column in columns:
                if f'"{column}"' in code or f"'{column}'" in code:
                    columns_used[table].append(column)
                    
        return columns_used 
"""
Spark code execution module for Spark PostgreSQL Agent.

This module provides functionality for executing PySpark code and extracting results.
"""

import os
import sys
import io
import re
import time
import json
import traceback
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import redirect_stdout, redirect_stderr

from pyspark.sql import SparkSession
import pyspark.sql.functions as F


@dataclass
class ExecutionResult:
    """
    Class representing the result of a code execution.
    
    Attributes:
        success: Whether the execution was successful
        code: The executed code
        result_data: The result data, if any
        error: Error message, if any
        execution_time: Time taken for execution
        transformation_id: Unique ID for this transformation
        request: The original request
    """
    success: bool = False
    code: Optional[str] = None
    result_data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    transformation_id: Optional[str] = None
    request: Optional[str] = None
    row_count: int = 0
    schema: Optional[str] = None


class SparkExecutor:
    """
    Executes PySpark code and manages the Spark session.
    
    This class handles:
    1. SparkSession initialization and management
    2. Code execution in a controlled environment
    3. Result extraction with different strategies
    4. Error handling and recovery
    """
    
    def __init__(self, postgres_config: Dict[str, Any] = None):
        """
        Initialize the SparkExecutor.
        
        Args:
            postgres_config: PostgreSQL connection configuration
        """
        self.postgres_config = postgres_config or {}
        self.spark_session = None
        self.execution_context = {}
        self.last_execution_result = None
        self.last_execution_time = 0
        self.last_execution_code = None
    
    def initialize_spark(self) -> SparkSession:
        """
        Initialize or get the Spark session.
        
        Returns:
            SparkSession instance
        """
        if self.spark_session:
            return self.spark_session
        
        # Create a new SparkSession
        self.spark_session = (
            SparkSession.builder
            .appName("SparkPGAgent")
            .config("spark.jars.packages", "org.postgresql:postgresql:42.2.18")
            .getOrCreate()
        )
        
        return self.spark_session
    
    def execute(self, code: str) -> ExecutionResult:
        """
        Execute PySpark code and extract results.
        
        Args:
            code: PySpark code to execute
            
        Returns:
            ExecutionResult object with execution results
        """
        # Store the code for reference
        self.last_execution_code = code
        
        # Track execution time
        start_time = time.time()
        
        # Prepare result
        result = ExecutionResult(
            success=False,
            code=code,
            execution_time=0,
        )
        
        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            # Ensure Spark session is initialized
            if not self.spark_session:
                self.initialize_spark()
            
            # Add common imports and utilities to the execution context
            self._prepare_execution_context()
            
            # Add necessary variables to the context
            local_context = self.execution_context.copy()
            
            # Add PostgreSQL config
            if self.postgres_config:
                local_context["postgres_config"] = self.postgres_config
                local_context["jdbc_url"] = f"jdbc:postgresql://{self.postgres_config.get('host', 'localhost')}:{self.postgres_config.get('port', 5432)}/{self.postgres_config.get('database', 'postgres')}"
                local_context["jdbc_properties"] = {
                    "user": self.postgres_config.get("user", "postgres"),
                    "password": self.postgres_config.get("password", "postgres"),
                    "driver": "org.postgresql.Driver"
                }
            
            # Add result tracking
            local_context["__result_df"] = None
            local_context["store_result"] = lambda df: self._store_result(local_context, df)
            
            # Process the code to detect result_df assignments
            modified_code = self._instrument_code(code)
            
            # Execute the code with stdout/stderr redirection
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(modified_code, local_context)
            
            # Extract stdout and stderr
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()
            
            # Try to find the result DataFrame
            found_result = self._extract_result(local_context, stderr_output)
            
            if found_result:
                # Extract schema and row count if possible
                schema_str = ""
                row_count = 0
                
                try:
                    if hasattr(found_result, "schema"):
                        schema_str = str(found_result.schema)
                    
                    if hasattr(found_result, "count"):
                        row_count = found_result.count()
                except:
                    pass
                
                # Convert result to JSON using collect() as fallback if pandas fails
                result_data = None
                try:
                    # Count rows before limiting for display
                    if hasattr(found_result, "count"):
                        row_count = found_result.count()
                        result.row_count = row_count
                    
                    # First try using pandas with limited rows
                    try:
                        if hasattr(found_result, "toPandas"):
                            pandas_df = found_result.limit(100).toPandas()
                            result_data = pandas_df.to_dict(orient="records")
                    except Exception as e:
                        stderr_output += f"\nPandas conversion failed, falling back to collect(): {str(e)}\n"
                        
                    # If pandas failed or wasn't available, use collect with limited rows
                    if result_data is None and hasattr(found_result, "collect"):
                        rows = found_result.limit(100).collect()
                        result_data = [row.asDict() for row in rows]
                        
                except Exception as e:
                    stderr_output += f"\nError converting result to JSON: {str(e)}\n"
                
                # Update result
                result.success = True
                result.result_data = found_result
                result.schema = schema_str
                result.row_count = row_count
            else:
                # No result found
                result.success = False
                result.error = "No result DataFrame found in the executed code."
        
        except Exception as e:
            # Execution failed
            error_msg = f"Execution error: {str(e)}\n{traceback.format_exc()}"
            result.success = False
            result.error = error_msg
            stderr_output = stderr_buffer.getvalue() + "\n" + error_msg
        
        finally:
            # Calculate execution time
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Store the result for reference
            self.last_execution_result = result
        
        return result
    
    def _prepare_execution_context(self) -> None:
        """Prepare the execution context with common imports and utilities"""
        context = {
            # Add Spark and SQL functions
            "spark": self.spark_session,
            "F": F,
            "SparkSession": SparkSession,
            
            # Utility functions
            "safe_col": lambda c: F.col(c) if isinstance(c, str) else c,
            "resolve_column": lambda df, c: f"`{c}`" if c in df.columns else c
        }
        
        self.execution_context = context
    
    def _instrument_code(self, code: str) -> str:
        """
        Instrument the code to detect result_df assignments.
        
        Args:
            code: Original code
            
        Returns:
            Modified code with result tracking
        """
        # Look for SparkSession creation (common in generated code)
        if "SparkSession.builder" in code:
            # Comment out SparkSession creation if it exists
            code = re.sub(
                r'(spark\s*=\s*SparkSession\.builder.*?\.getOrCreate\(\))',
                r'# \1  # Using existing SparkSession',
                code,
                flags=re.DOTALL
            )
            print("DEBUG: Commented out SparkSession creation")
        
        # Look for result_df assignment
        if "result_df" in code:
            # Find the last assignment to result_df
            matches = list(re.finditer(r'^result_df\s*=', code, re.MULTILINE))
            if matches:
                last_match = matches[-1]
                # Insert code to store the result
                code_lines = code.split('\n')
                assignment_line = last_match.start() // (len(code_lines[0]) + 1)  # Rough estimate of line number
                if 0 <= assignment_line < len(code_lines):
                    indentation = re.match(r'^\s*', code_lines[assignment_line]).group(0)
                    code_lines.insert(assignment_line + 1, f"{indentation}store_result(result_df)")
                    code = '\n'.join(code_lines)
                    print("DEBUG: Found result_df assignment in code, wrapping with store_result()")
        
        return code
    
    def _store_result(self, context: Dict[str, Any], df) -> None:
        """
        Store a result DataFrame in the execution context.
        
        Args:
            context: Execution context
            df: DataFrame to store
        """
        context["__result_df"] = df
    
    def _extract_result(self, local_context: Dict[str, Any], stderr: str) -> Optional[Any]:
        """
        Extract the result DataFrame from the execution context.
        
        Args:
            local_context: Local execution context
            stderr: Standard error output
            
        Returns:
            Result DataFrame or None if not found
        """
        # Strategy 1: Check for explicitly stored result
        if "__result_df" in local_context and local_context["__result_df"] is not None:
            print("DEBUG: Found result in __result_df")
            return local_context["__result_df"]
        
        # Strategy 2: Look for result_df in the context
        if "result_df" in local_context:
            print("DEBUG: Found result_df in execution context")
            return local_context["result_df"]
        
        # Strategy 3: Look for any DataFrame objects in the context
        df_vars = []
        for var_name, var_value in local_context.items():
            # Skip special variables and functions
            if var_name.startswith("__") or callable(var_value):
                continue
                
            # Check if it looks like a DataFrame
            if hasattr(var_value, "show") and hasattr(var_value, "select"):
                df_vars.append((var_name, var_value))
        
        if df_vars:
            # Sort by likelihood of being the result (heuristic)
            candidates = sorted(df_vars, key=lambda x: (
                # Variables with 'result' in the name are more likely
                0 if "result" in x[0].lower() else 1,
                # Variables defined later are more likely to be the result
                -local_context.get("__var_order", {}).get(x[0], 0)
            ))
            
            # Return the most likely candidate
            print(f"DEBUG: Found potential result DataFrame: {candidates[0][0]}")
            return candidates[0][1]
        
        # No result found
        return None
    
    def shutdown(self) -> None:
        """Stop the Spark session"""
        if self.spark_session:
            self.spark_session.stop()
            self.spark_session = None
    
    def get_schema_info(self) -> str:
        """
        Get database schema information from PostgreSQL.
        
        Returns:
            String with schema information
        """
        if not self.spark_session:
            self.initialize_spark()
        
        try:
            # Create JDBC URL
            jdbc_url = f"jdbc:postgresql://{self.postgres_config.get('host', 'localhost')}:{self.postgres_config.get('port', 5432)}/{self.postgres_config.get('database', 'postgres')}"
            jdbc_properties = {
                "user": self.postgres_config.get("user", "postgres"),
                "password": self.postgres_config.get("password", "postgres"),
                "driver": "org.postgresql.Driver"
            }
            
            # Get a list of tables
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            
            tables_df = self.spark_session.read.jdbc(
                url=jdbc_url,
                table=f"({tables_query}) AS tables_query",
                properties=jdbc_properties
            )
            
            tables = [row.table_name for row in tables_df.collect()]
            
            # Build schema information string
            schema_info = "Database Schema:\n"
            
            for table in tables:
                schema_info += f"Table: {table}\n"
                
                # Get column information
                columns_query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table}'
                    ORDER BY ordinal_position
                """
                
                columns_df = self.spark_session.read.jdbc(
                    url=jdbc_url,
                    table=f"({columns_query}) AS columns_query",
                    properties=jdbc_properties
                )
                
                for row in columns_df.collect():
                    nullable = "NULL" if row.is_nullable == "YES" else "NOT NULL"
                    schema_info += f"  Column: {row.column_name}, Type: {row.data_type}, {nullable}\n"
                
                schema_info += "\n"
            
            return schema_info
            
        except Exception as e:
            error_msg = f"Error getting schema info: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return f"Schema information unavailable: {str(e)}" 
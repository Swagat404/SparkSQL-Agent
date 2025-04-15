"""
Code generation phases for the LLM compiler.

This module contains all the code generation variants:
1. Standard code generation (default)
2. Context-aware code generation (for related requests)
3. Error-aware code generation (when previous errors occurred)
4. Refinement code generation (for user refinement requests)
"""

import json
import re
from typing import Dict, Any, Set

from spark_pg_agent_formal.core.context import CompilationContext
from spark_pg_agent_formal.llm.providers import LLMProvider


def standard_code_generation(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> CompilationContext:
    """
    STANDARD code generation phase - Called when no special context exists.
    
    Args:
        context: CompilationContext object with compilation state
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Updated CompilationContext
    """
    from spark_pg_agent_formal.llm.utils.utils import extract_code_from_response, log_to_file
    from spark_pg_agent_formal.llm.utils.code_validation import validate_and_fix_code
    
    # Update current phase
    context.current_phase = "code_generation"
    
    # Get PostgreSQL connection details
    if context.postgres_config:
        pg_host = context.postgres_config.get("host", "localhost")
        pg_port = context.postgres_config.get("port", 5432)
        pg_db = context.postgres_config.get("database", "postgres")
        pg_user = context.postgres_config.get("user", "postgres")
        pg_pass = context.postgres_config.get("password", "postgres")
    else:
        pg_host = "localhost"
        pg_port = 5432
        pg_db = "postgres"
        pg_user = "postgres"
        pg_pass = "postgres"
        
    # Create the base prompt for code generation
    prompt = f"""
    You are writing PySpark code to implement the following transformation:
    
    Request: "{context.user_request}"
    
    Execution Plan:
    {context.execution_plan}
    
    PostgreSQL Connection Details:
    Host: {pg_host}
    Port: {pg_port}
    Database: {pg_db}
    User: {pg_user}
    Password: {pg_pass}
    
    Table Information:
    """
    
    # Add table schema information
    for table_name in context.tables_referenced:
        schema = context.schema_memory.get_table_schema(table_name)
        if schema:
            prompt += f"""
Table: {table_name}
Columns:
"""
            for col_name, col_type in schema.columns.items():
                prompt += f"- {col_name}: {col_type}\n"
            
            if schema.primary_keys:
                prompt += f"Primary Keys: {', '.join(schema.primary_keys)}\n"
            
            if schema.foreign_keys:
                prompt += "Foreign Keys:\n"
                for fk_col, (ref_table, ref_col) in schema.foreign_keys.items():
                    prompt += f"- {fk_col} references {ref_table}.{ref_col}\n"
            
            prompt += "\n"
    
    # Check if we should include previous transformation details
    if "previous_transformation" in context.phase_results:
        prev_transform = context.phase_results["previous_transformation"]
        prompt += f"""
        PREVIOUS TRANSFORMATION CONTEXT:
        Previous Request: "{prev_transform['request']}"
        
        Previous Code Structure:
        ```python
        {prev_transform['code'][:1000] + '...' if len(prev_transform['code']) > 1000 else prev_transform['code']}
        ```
        
        This new request builds upon or is related to the previous transformation.
        Consider reusing patterns and structure from the previous code where applicable.
        """
        
        # Include result structure if available
        if "result_structure" in prev_transform:
            prompt += f"""
            Previous result columns: {prev_transform['result_structure']['columns']}
            Consider how the previous output structure relates to this new request.
            """
    
    prompt += """
    IMPORTANT SCHEMA DETAILS:
    - The "customers" table has columns: customer_id, name, email, country (it does NOT have first_name/last_name)
    - The "orders" table has columns: order_id, customer_id, order_date, total_amount
    - Joins must use qualified column references, e.g., customers_df["customer_id"] == orders_df["customer_id"]
    - Use F.col() for column references in aggregations, e.g., F.sum(F.col("total_amount"))
    
    Guidelines for implementation:
    1. Use PySpark SQL functions (import as F) and DataFrame operations
    2. Load data from PostgreSQL using JDBC
    3. Implement the transformation following the execution plan
    4. Make sure to handle errors gracefully
    5. Store the FINAL result in a DataFrame variable named 'result_df'
    6. Make sure to select appropriate columns in the final result
    7. For joins, explicitly specify join columns with equality conditions and ALWAYS include the join type
    8. Document your code with clear comments
    
    IMPORTANT: For a complete implementation, include:
    1. Necessary imports
    2. SparkSession creation (but make it optional/commented out as it may already exist)
    3. JDBC connection details
    4. Table loading functions
    5. All transformation steps
    6. Final result selection
    7. Result display (result_df.show())
    
    Provide clean, production-quality code.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "CODE_GENERATION", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "CODE_GENERATION_RESPONSE", "", response)
    
    # Extract code from the response
    code = extract_code_from_response(response)
    
    # Validate and fix the code before returning
    fixed_code = validate_and_fix_code(code)
    
    # Store generated code in context
    context.phase_results["code_generation"] = {"code": fixed_code, "full_response": response}
    
    return context


def context_aware_code_generation(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> CompilationContext:
    """
    Generate PySpark code based on previous context and current request.
    
    Args:
        context: CompilationContext object with compilation state
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Updated CompilationContext
    """
    from spark_pg_agent_formal.llm.utils.utils import extract_code_from_response, log_to_file
    
    # Update current phase
    context.current_phase = "code_generation"
    
    # Get previous code from context
    previous_code = context.phase_results.get("previous_code", "")
    previous_request = context.phase_results.get("previous_request", "")
    
    # Create prompt for context-aware code generation
    prompt = f"""
    You are modifying existing PySpark code to implement a new transformation that is related to the previous one.
    
    Previous Request: "{previous_request}"
    Current Request: "{context.user_request}"
    
    Execution Plan for Current Request:
    {context.execution_plan}
    
    Previous Code (WORKING CORRECTLY):
    ```python
    {previous_code}
    ```
    
    IMPORTANT GUIDELINES:
    1. Keep the working parts of the previous code.
    2. When adding columns or modifying the existing code:
       - ALWAYS qualify column references with table aliases 
       - For any column that appears in multiple tables, qualification is MANDATORY
    3. Maintain correct indentation - especially with SparkSession definition
    4. Preserve the same variable names and DataFrame structure
    5. Store the FINAL result in a DataFrame variable named 'result_df'
    
    COMMON ERRORS TO AVOID:
    - Ambiguous column references - qualify ALL column references with table aliases
    - Incorrect indentation - especially at the beginning of SparkSession creation
    - Incomplete joins - ensure join conditions are fully specified
    
    Generate the complete, modified PySpark code (not just the changes):
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "CONTEXT_AWARE_CODE_GENERATION", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "CONTEXT_AWARE_CODE_GENERATION_RESPONSE", "", response)
    
    # Extract code from the response
    code = extract_code_from_response(response)
    
    # Store generated code in context
    context.phase_results["code_generation"] = {"code": code, "full_response": response, "is_context_aware": True}
    
    return context


def error_aware_code_generation(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> CompilationContext:
    """
    Generate code with awareness of previous errors.
    
    Args:
        context: CompilationContext object with compilation state
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Updated CompilationContext
    """
    from spark_pg_agent_formal.llm.utils.utils import extract_code_from_response, log_to_file
    from spark_pg_agent_formal.llm.utils.code_validation import validate_and_fix_code
    
    # Extract previous errors
    previous_errors = context.phase_results.get("previous_errors", [])
    
    # Get PostgreSQL connection details
    if context.postgres_config:
        pg_host = context.postgres_config.get("host", "localhost")
        pg_port = context.postgres_config.get("port", 5432)
        pg_db = context.postgres_config.get("database", "postgres")
        pg_user = context.postgres_config.get("user", "postgres")
        pg_pass = context.postgres_config.get("password", "postgres")
    else:
        pg_host = "localhost"
        pg_port = 5432
        pg_db = "postgres"
        pg_user = "postgres"
        pg_pass = "postgres"
        
    # Format previous error information
    error_history = ""
    
    # Identify common error patterns
    error_patterns = {
        "ambiguous_reference": {"detected": False, "columns": set(), "count": 0},
        "column_not_exist": {"detected": False, "columns": set(), "count": 0},
        "indentation_error": {"detected": False, "lines": set(), "count": 0},
        "syntax_error": {"detected": False, "details": set(), "count": 0},
        "not_found": {"detected": False, "symbols": set(), "count": 0},
        "type_error": {"detected": False, "details": set(), "count": 0}
    }
    
    # Extract the last code that failed for potential reuse
    last_code = ""
    for err in previous_errors:
        if err.get('code', ''):
            last_code = err.get('code', '')
    
    for i, err in enumerate(previous_errors):
        error_text = err.get('error', '')
        error_history += f"\nAttempt {i+1}:\n"
        error_history += f"Error: {error_text}\n"
        
        # Check for common error patterns with detailed extraction
        if "ambiguous" in error_text.lower():
            error_patterns["ambiguous_reference"]["detected"] = True
            error_patterns["ambiguous_reference"]["count"] += 1
            
            # Extract column names
            col_match = re.search(r"Reference [\"']?([^\"']+)[\"']? is ambiguous", error_text)
            if col_match:
                error_patterns["ambiguous_reference"]["columns"].add(col_match.group(1))
        
        if "cannot be resolved" in error_text.lower() or "does not exist" in error_text.lower():
            error_patterns["column_not_exist"]["detected"] = True
            error_patterns["column_not_exist"]["count"] += 1
            
            col_match = re.search(r"[\"']([^\"']+)[\"']", error_text)
            if col_match:
                error_patterns["column_not_exist"]["columns"].add(col_match.group(1))
        
        if "indentation" in error_text.lower() or "unexpected indent" in error_text.lower():
            error_patterns["indentation_error"]["detected"] = True
            error_patterns["indentation_error"]["count"] += 1
            
            # Try to extract line info
            line_match = re.search(r"line (\d+)", error_text)
            if line_match:
                error_patterns["indentation_error"]["lines"].add(line_match.group(1))
        
        if "syntax" in error_text.lower():
            error_patterns["syntax_error"]["detected"] = True
            error_patterns["syntax_error"]["count"] += 1
            
            # Try to extract specific syntax error
            syntax_detail = re.search(r"(unexpected|invalid|expected) ([^:]+)", error_text)
            if syntax_detail:
                error_patterns["syntax_error"]["details"].add(syntax_detail.group(0))
        
        # Add limited code snippet
        if err.get('code'):
            # Show a more targeted code snippet that focuses on the likely error area
            code_snippet = err['code']
            
            # If we have line info, try to show that section
            if error_patterns["indentation_error"]["lines"]:
                lines = code_snippet.split('\n')
                line_num = next(iter(error_patterns["indentation_error"]["lines"]))
                try:
                    line_idx = int(line_num) - 1
                    start_idx = max(0, line_idx - 2)
                    end_idx = min(len(lines), line_idx + 3)
                    code_snippet = '\n'.join(lines[start_idx:end_idx])
                except (ValueError, IndexError):
                    # Fall back to showing the beginning
                    code_snippet = '\n'.join(code_snippet.split('\n')[:7])
            else:
                # Default: Show first few lines which often contain the problematic code
                code_snippet = '\n'.join(code_snippet.split('\n')[:7])
                
            error_history += f"Code snippet:\n```\n{code_snippet}\n```\n"
    
    # Create detailed error analysis for the prompt
    error_analysis = []
    if error_patterns["ambiguous_reference"]["detected"]:
        columns_list = ', '.join(f'`{col}`' for col in error_patterns["ambiguous_reference"]["columns"])
        error_analysis.append(f"- Ambiguous column references detected: you must use table qualification for all references")
        if columns_list:
            error_analysis.append(f"  Affected columns: {columns_list}")
    
    if error_patterns["column_not_exist"]["detected"]:
        columns_list = ', '.join(f'`{col}`' for col in error_patterns["column_not_exist"]["columns"])
        error_analysis.append(f"- Column not found errors detected: verify all column names against the schema")
        if columns_list:
            error_analysis.append(f"  Missing columns: {columns_list}")
    
    if error_patterns["indentation_error"]["detected"]:
        error_analysis.append(f"- Indentation errors detected: fix indentation especially for multi-line constructs")
        if error_patterns["indentation_error"]["lines"]:
            lines_list = ', '.join(error_patterns["indentation_error"]["lines"])
            error_analysis.append(f"  Problem occurred around line(s): {lines_list}")
    
    if error_patterns["syntax_error"]["detected"]:
        error_analysis.append(f"- Syntax errors detected: verify all PySpark syntax is correct")
        if error_patterns["syntax_error"]["details"]:
            details_list = ', '.join(error_patterns["syntax_error"]["details"])
            error_analysis.append(f"  Syntax issues: {details_list}")
    
    # Create a prompt that includes previous errors and detailed analysis
    prompt = f"""
    You are generating PySpark code to implement a database transformation.
    
    User Request: "{context.user_request}"
    
    Execution Plan:
    {context.execution_plan}
    
    PREVIOUS FAILED ATTEMPTS:
    {error_history}
    
    DETAILED ERROR ANALYSIS:
    {chr(10).join(error_analysis)}
    
    
    CODE STRUCTURE REQUIREMENTS:
    1. For SparkSession creation, use this pattern:
       spark = SparkSession.builder\\
           .appName("App Name")\\
           .getOrCreate()
       
    2. For all column references in joins or conditions, ALWAYS use fully qualified table aliases
       Example: df1["column"] == df2["column"]
    
    3. For every join, use explicit equality conditions
       Example: df1.join(df2, df1["id"] == df2["id"], "inner")
    
    4. Final output must store results in variable named 'result_df'
    
    Generate a complete, executable PySpark code that implements the requested transformation
    while avoiding the previously identified errors:
    """
    
    # If we have last_code and it doesn't have major syntax issues, use it as a starting point
    if last_code and not (error_patterns["syntax_error"]["count"] > 2):
        # Extract the core structure while removing known problematic sections
        prompt += f"""
        Use the structure of this previous attempt as a starting point, but fix the identified errors:
        ```python
        {last_code}
        ```
        """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "ERROR_AWARE_CODE_GENERATION", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "ERROR_AWARE_CODE_GENERATION_RESPONSE", "", response)
    
    # Extract code from the response
    code = extract_code_from_response(response)
    
    # Validate and fix the code before returning
    fixed_code = validate_and_fix_code(code)
    
    # Store generated code in context
    context.phase_results["code_generation"] = {"code": fixed_code, "full_response": response, "is_error_aware": True}
    
    return context


def refinement_code_generation(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> CompilationContext:
    """
    Generate code based on a refinement request after user rejection.
    
    Args:
        context: CompilationContext object with compilation state
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Updated CompilationContext
    """
    from spark_pg_agent_formal.llm.utils.utils import extract_code_from_response, log_to_file
    from spark_pg_agent_formal.llm.utils.code_validation import validate_and_fix_code
    
    # Update current phase
    context.current_phase = "code_generation"
    
    # Get refinement context
    refinement_context = context.phase_results.get("refinement_context", {})
    original_request = refinement_context.get("original_request", "")
    original_code = refinement_context.get("original_code", "")
    original_result_summary = context.phase_results.get("original_result_summary", {})
    
    # Extract previous errors if any
    previous_errors = context.phase_results.get("previous_errors", [])
    
    # Get PostgreSQL connection details
    if context.postgres_config:
        pg_host = context.postgres_config.get("host", "localhost")
        pg_port = context.postgres_config.get("port", 5432)
        pg_db = context.postgres_config.get("database", "postgres")
        pg_user = context.postgres_config.get("user", "postgres")
        pg_pass = context.postgres_config.get("password", "postgres")
    else:
        pg_host = "localhost"
        pg_port = 5432
        pg_db = "postgres"
        pg_user = "postgres"
        pg_pass = "postgres"
    
    # Identify common error patterns like we do in error-aware code generation
    error_patterns = {
        "ambiguous_reference": {"detected": False, "columns": set(), "count": 0},
        "column_not_exist": {"detected": False, "columns": set(), "count": 0},
        "indentation_error": {"detected": False, "lines": set(), "count": 0},
        "syntax_error": {"detected": False, "details": set(), "count": 0},
        "not_found": {"detected": False, "symbols": set(), "count": 0},
        "type_error": {"detected": False, "details": set(), "count": 0}
    }
    
    # Process previous errors to extract patterns
    error_history = ""
    if previous_errors:
        for i, err in enumerate(previous_errors):
            error_text = err.get('error', '')
            error_history += f"\nAttempt {i+1}:\n"
            error_history += f"Error: {error_text}\n"
            
            # Check for common error patterns
            if "ambiguous" in error_text.lower():
                error_patterns["ambiguous_reference"]["detected"] = True
                error_patterns["ambiguous_reference"]["count"] += 1
                col_match = re.search(r"Reference [\"']?([^\"']+)[\"']? is ambiguous", error_text)
                if col_match:
                    error_patterns["ambiguous_reference"]["columns"].add(col_match.group(1))
            
            if "cannot be resolved" in error_text.lower() or "does not exist" in error_text.lower():
                error_patterns["column_not_exist"]["detected"] = True
                error_patterns["column_not_exist"]["count"] += 1
                col_match = re.search(r"[\"']([^\"']+)[\"']", error_text)
                if col_match:
                    error_patterns["column_not_exist"]["columns"].add(col_match.group(1))
            
            if "indentation" in error_text.lower() or "unexpected indent" in error_text.lower():
                error_patterns["indentation_error"]["detected"] = True
                error_patterns["indentation_error"]["count"] += 1
                line_match = re.search(r"line (\d+)", error_text)
                if line_match:
                    error_patterns["indentation_error"]["lines"].add(line_match.group(1))
    
    # Create error analysis for the prompt
    error_analysis = []
    if error_patterns["ambiguous_reference"]["detected"]:
        columns_list = ', '.join(f'`{col}`' for col in error_patterns["ambiguous_reference"]["columns"])
        error_analysis.append(f"- Ambiguous column references detected for columns: {columns_list}")
    
    if error_patterns["column_not_exist"]["detected"]:
        columns_list = ', '.join(f'`{col}`' for col in error_patterns["column_not_exist"]["columns"])
        error_analysis.append(f"- Column not found errors for columns: {columns_list}")
    
    if error_patterns["indentation_error"]["detected"]:
        error_analysis.append(f"- Indentation errors detected in previous attempts")
    
    error_analysis_text = "\n".join(error_analysis) if error_analysis else "No specific errors detected in previous attempts."
    
    # Create prompt for refinement code generation
    prompt = f"""
    You are refining PySpark code based on user feedback. The user rejected the previous transformation result
    and has provided a new request that indicates what needs to be changed.
    
    Original Request: "{original_request}"
    New Refinement Request: "{context.user_request}"
    
    Original Code:
    ```python
    {original_code}
    ```
    
    Original Result Summary:
    {json.dumps(original_result_summary, indent=2) if original_result_summary else "No result summary available."}
    
    Current Execution Plan:
    {context.execution_plan}
    
    ERROR ANALYSIS FROM PREVIOUS ATTEMPTS:
    {error_analysis_text}
    
    KEY REQUIREMENTS:
    1. For all column references in joins or conditions, ALWAYS use fully qualified table aliases
       Example: df1["column"] == df2["column"]
    
    2. For multi-line statements, especially SparkSession creation and method chaining, use consistent indentation:
       spark = SparkSession.builder\\
           .appName("App Name")\\
           .getOrCreate()
    
    3. For every join, use explicit equality conditions
       Example: df1.join(df2, df1["id"] == df2["id"], "inner")
    
    USER FEEDBACK ANALYSIS:
    The user rejected the previous transformation and is now asking: "{context.user_request}"
    This likely means they want to:
    1. Modify the output columns or ordering
    2. Fix an error in the calculation or logic
    3. Add missing information that was expected but not included
    
    Generate complete, executable PySpark code that addresses the user's refinement request.
    Maintain the core structure of the original code but modify it according to the new requirements.
    Pay special attention to avoiding the errors identified in previous attempts.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "REFINEMENT_CODE_GENERATION", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "REFINEMENT_CODE_GENERATION_RESPONSE", "", response)
    
    # Extract code from the response
    code = extract_code_from_response(response)
    
    # Validate and fix the code before returning
    fixed_code = validate_and_fix_code(code)
    
    # Store generated code in context
    context.phase_results["code_generation"] = {"code": fixed_code, "full_response": response, "is_refinement": True}
    
    return context 
"""
Schema analysis phase for the LLM compiler.

This module is responsible for analyzing the database schema and determining 
which tables and columns are needed for a given transformation request.
"""

import json
import re
import traceback
from typing import List, Callable, Dict, Any

from spark_pg_agent_formal.core.context import CompilationContext
from spark_pg_agent_formal.llm.providers import LLMProvider
from spark_pg_agent_formal.db.schema_memory import SchemaMemory


def schema_analysis(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str,
    extract_tables_func: Callable
) -> CompilationContext:
    """
    Phase 1: Analyze the schema to identify required tables and columns.
    
    Args:
        context: The compilation context
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        extract_tables_func: Function to extract tables from text
        
    Returns:
        Updated compilation context
    """
    from spark_pg_agent_formal.llm.utils.utils import log_to_file
    
    # Update current phase
    context.current_phase = "schema_analysis"
    
    # Get the formatted schema
    schema_text = context.schema_memory.format_schema_for_prompt()
    
    # Create prompt for schema analysis
    prompt = f"""
    You are analyzing a database schema to identify the tables and columns needed for a transformation.
    
    Request: "{context.user_request}"
    
    {schema_text}
    """
    
    # Add context from previous transformation if available
    if "previous_transformation" in context.phase_results:
        prev_transform = context.phase_results["previous_transformation"]
        
        prompt += f"""
        This request appears to be related to a previous transformation:
        Previous Request: "{prev_transform['request']}"
        
        Tables used in previous transformation: {', '.join(prev_transform['tables'])}
        Columns used: {json.dumps(prev_transform['columns'], indent=2) if 'columns' in prev_transform else 'Not available'}
        
        If this new request builds on the previous one, consider using similar tables and join patterns.
        """
    
    # If this is a relative request, add context about previous transformation
    if "previous_request" in context.phase_results:
        previous_request = context.phase_results["previous_request"]
        previous_code = context.phase_results.get("previous_code", "")
        memory_context = context.phase_results.get("memory_context", {})
        
        # If we have a referenced transformation from memory, add that context
        if "referenced_transformation" in context.phase_results:
            ref_transform = context.phase_results["referenced_transformation"]
            ref_type = context.phase_results.get("reference_type", "a previous step")
            
            prompt += f"""
            This request explicitly references {ref_type}:
            Referenced Request: "{ref_transform.get('request', '')}"
            Step Number: {ref_transform.get('step_number', 'unknown')}
            
            Tables used in referenced transformation: {', '.join(ref_transform.get('tables_used', []))}
            
            You should prioritize using the same tables and similar structure from this referenced transformation.
            """
            
            # If we have result summary from the referenced transformation, include it
            if "previous_result_summary" in context.phase_results:
                result_summary = context.phase_results["previous_result_summary"]
                prompt += f"""
                The referenced transformation produced results with these characteristics:
                Row count: {result_summary.get('row_count', 'unknown')}
                Columns: {result_summary.get('columns', [])}
                
                This information should guide your understanding of the data structure.
                """
        # Regular relative transformation reference
        else:
            prompt += f"""
            This request appears to be relative to a previous transformation:
            Previous Request: "{previous_request}"
            
            {f"Previous Code: ```\n{previous_code}\n```" if previous_code else ""}
            
            Implied intentions from context: {memory_context.get('implied_intentions', [])}
            Current focus entities: {memory_context.get('entity_focus', [])}
            """
            
            # If we have a specific referenced entity, highlight it
            if "referenced_entity" in context.phase_results:
                entity = context.phase_results["referenced_entity"]
                prompt += f"""
                This request specifically references the entity: "{entity}"
                You should ensure this entity is included in your schema analysis.
                """
                
            # If we have a filter request, note that
            if memory_context.get("filter_requested"):
                filter_value = memory_context.get("potential_filter_value", "unknown")
                prompt += f"""
                This appears to be a filtering request, possibly filtering by: {filter_value}
                You should include columns that would allow this filtering operation.
                """
    
    prompt += """
    Based on the request and schema, please identify:
    1. Which tables are needed for this transformation
    2. Which columns from each table are needed
    3. Any joins that will be required between tables
    
    Format your response as JSON with the following structure:
    {
        "tables": ["table1", "table2"],
        "columns": {"table1": ["col1", "col2"], "table2": ["col1", "col3"]},
        "joins": [
            {"left_table": "table1", "left_column": "id", "right_table": "table2", "right_column": "table1_id"}
        ],
        "explanation": "Brief explanation of your analysis"
    }
    
    Use only the tables and columns mentioned in the schema.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "SCHEMA_ANALYSIS", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "SCHEMA_ANALYSIS_RESPONSE", "", response)
    
    # Extract JSON from response
    try:
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find any JSON-like structure
            json_match = re.search(r'({.*})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
        
        analysis = json.loads(json_str)
        
        # Update context with extracted information
        context.tables_referenced = analysis.get("tables", [])
        context.columns_referenced = analysis.get("columns", {})
        context.joins = analysis.get("joins", [])
        
        # Store schema analysis results
        context.phase_results["schema_analysis"] = analysis
        
    except Exception as e:
        print(f"Error parsing schema analysis: {str(e)}")
        traceback.print_exc()
        context.phase_results["schema_analysis_error"] = str(e)
        
        # Create a fallback analysis by extracting table names
        context.tables_referenced = extract_tables_func(response, context.schema_memory)
        context.phase_results["schema_analysis"] = {
            "tables": context.tables_referenced,
            "error": str(e)
        }
    
    return context 
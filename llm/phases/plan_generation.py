"""
Plan generation phase for the LLM compiler.

This module is responsible for generating an execution plan for the transformation
based on the schema analysis results.
"""

import json
from typing import Dict, Any

from spark_pg_agent_formal.core.context import CompilationContext
from spark_pg_agent_formal.llm.providers import LLMProvider


def plan_generation(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> CompilationContext:
    """
    Phase 2: Generate an execution plan for the transformation.
    
    Args:
        context: The compilation context
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Updated compilation context
    """
    from spark_pg_agent_formal.llm.utils.utils import log_to_file
    
    # Update current phase
    context.current_phase = "plan_generation"
    
    # Format the known tables and columns
    tables_str = str(context.tables_referenced)
    columns_by_table = json.dumps(context.columns_referenced, indent=2)
    
    # Format table schemas for prompt
    table_schemas = {}
    for table_name in context.tables_referenced:
        schema = context.schema_memory.get_table_schema(table_name)
        if schema:
            table_schemas[table_name] = {
                "columns": schema.columns,
                "primary_keys": schema.primary_keys,
                "foreign_keys": {k: list(v) for k, v in schema.foreign_keys.items()}
            }
    table_schemas_str = json.dumps(table_schemas, indent=2)
    
    # Format joins info
    joins_str = json.dumps(context.joins, indent=2)
    
    # Add previous transformation context if available
    previous_plan = ""
    if "previous_transformation" in context.phase_results and "execution_plan" in context.phase_results["previous_transformation"]:
        prev_transform = context.phase_results["previous_transformation"]
        previous_plan = f"""
        Previous transformation execution plan:
        {prev_transform['execution_plan']}
        
        If this request builds upon the previous transformation, consider adapting its execution plan.
        """
    
    # Create prompt for execution plan generation
    prompt = f"""
    You are designing an execution plan for a PySpark transformation.
    
    Request: "{context.user_request}"
    
    Based on schema analysis, the following tables and columns are needed:
    Tables: {tables_str}
    
    Columns by table:
    {columns_by_table}
    
    Table schemas:
    {table_schemas_str}
    
    Identified joins:
    {joins_str}
    
    {previous_plan}
    
    Please create a step-by-step execution plan that outlines:
    1. How to load the necessary tables
    2. What transformations to apply (filters, joins, aggregations, etc.)
    3. The order of operations
    4. What the final output should look like
    
    Format your response as a numbered list of steps, followed by a summary.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "PLAN_GENERATION", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "PLAN_GENERATION_RESPONSE", "", response)
    
    # Store the execution plan in the context
    context.execution_plan = response
    context.phase_results["plan_generation"] = {"plan": response}
    
    return context 
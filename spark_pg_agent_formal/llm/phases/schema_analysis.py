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
    
    # First, check if we have past queries to analyze
    past_queries = context.phase_results.get("past_queries", [])
    
    # Token-efficient two-stage approach:
    # 1. First determine which query (if any) is relevant using just the prompts
    # 2. Then get detailed information only for the relevant query
    
    should_apply_context = False
    referenced_query_id = None
    referenced_transform = None
    
    # Stage 1: Determine relevance if we have past queries
    if past_queries and len(past_queries) > 0:
        # Analyze relationship with just the prompts (token-efficient)
        context_analysis = analyze_context_relationship(
            context.user_request, 
            past_queries, 
            llm_provider,
            enable_logging,
            log_file
        )
        
        # Store the context analysis in the compilation context
        context.phase_results["context_analysis"] = context_analysis
        
        # Only apply previous context if the LLM determined it's appropriate
        should_apply_context = context_analysis.get("requires_context", False)
        referenced_query_id = context_analysis.get("relevant_query_id", None)
        
        # If this is a refinement query (after user selected 'n' on feedback)
        if context.phase_results.get("is_refinement", False):
            # For refinements, we almost always want to maintain context
            should_apply_context = True
            # Use the most recent transformation as reference
            referenced_query_id = past_queries[0].get("id") if past_queries else None
    
    # Stage 2: If we need context, fetch the detailed information for just that query
    if should_apply_context and referenced_query_id and hasattr(context, "memory"):
        # Get detailed information about the specific relevant query
        referenced_transform = context.memory.get_transformation_details(referenced_query_id)
        if referenced_transform:
            context.phase_results["referenced_transformation"] = referenced_transform
    
    # Get the formatted schema
    schema_text = context.schema_memory.format_schema_for_prompt()
    
    # Create prompt for schema analysis
    prompt = f"""
    You are analyzing a database schema to identify the tables and columns needed for a transformation.
    
    Request: "{context.user_request}"
    
    {schema_text}
    """
    
    # Add context from previous transformation if appropriate
    if should_apply_context and referenced_transform:
        # Store context relationship information
        context_analysis = context.phase_results.get("context_analysis", {})
            
        prompt += f"""
        This request is related to a previous transformation:
        Previous Request: "{referenced_transform.get('request', '')}"
        
        Tables used in previous transformation: {', '.join(referenced_transform.get('tables_used', []))}
        Columns used: {json.dumps(referenced_transform.get('columns_used', {}), indent=2) if 'columns_used' in referenced_transform else 'Not available'}
        
        Relationship to previous query: {context_analysis.get('relationship_type', 'Unknown')}
        Context explanation: {context_analysis.get('explanation', 'This query builds on the previous one.')}
        
        Use this context to guide your schema analysis.
        """
        
        # If we have result summary, include it
        if "result_summary" in referenced_transform:
            result_summary = referenced_transform["result_summary"]
            prompt += f"""
            The referenced transformation produced results with these characteristics:
            Row count: {result_summary.get('row_count', 'unknown')}
            Columns: {result_summary.get('columns', [])}
            Sample data: {json.dumps(result_summary.get('sample_data', [])[:2], indent=2) if 'sample_data' in result_summary else 'Not available'}
            
            This information should guide your understanding of the data structure.
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


def analyze_context_relationship(
    current_query: str,
    past_queries: List[Dict[str, Any]],
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str
) -> Dict[str, Any]:
    """
    Analyzes the relationship between the current query and previous queries.
    Token-efficient implementation that only works with query prompts.
    
    Args:
        current_query: The current user query
        past_queries: List of past queries with minimal information
        llm_provider: The LLM provider
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        
    Returns:
        Dict containing context analysis
    """
    from spark_pg_agent_formal.llm.utils.utils import log_to_file
    
    # Print debug information about context analysis
    print("\n" + "="*80)
    print(f"🔍 CONTEXT ANALYSIS STARTED for: '{current_query}'")
    print(f"📚 Available previous queries: {len(past_queries)}")
    for i, query in enumerate(past_queries):
        query_num = i + 1
        print(f"  Query #{query_num} (ID: {query.get('id', 'unknown')}): '{query.get('request', '')}'")
    print("-"*80)
    
    # If no history, no context to apply
    if not past_queries:
        print("❌ No previous queries available - using NO context")
        return {
            "requires_context": False,
            "explanation": "No previous queries available"
        }
    
    # Create prompt for context analysis - using only query prompts for efficiency
    prompt = f"""
    You are analyzing SQL transformation requests to determine context relationships.
    You should be conservative about applying context from previous queries, but recognize common continuity patterns.
    
    Current query: "{current_query}"
    
    Previous queries:
    """
    
    # Add just the query prompts - no additional metadata to save tokens
    for i, query in enumerate(past_queries):
        query_num = i + 1
        prompt += f"""
        Query #{query_num} (ID: {query.get('id', 'unknown')}): "{query.get('request', '')}"
        """
    
    prompt += """
    Determine if the current query:
    1) Is self-contained and requires no previous context (DEFAULT)
    2) Builds directly on the previous query (most recent) with reference
    3) References a specific earlier query with reference
    4) References a "first" or other ordinal transformation
    
    IMPORTANT: Be balanced in your assessment. The default should be to treat queries as self-contained,
    but recognize both explicit and implicit references to previous queries.
    
    Consider these as valid references to previous work:
    - Explicit markers like "from the first transformation", "based on previous query", etc.
    - Direct references to previous query numbers or IDs
    - References to "previous/last/first result", "previous output", etc.
    - Phrases like "give me the same", "now show me the same", or "similar to before" that clearly reference previous work
    - Phrases with "these" or "those" when referring to entities from previous queries
    - Phrases like "but only for..." or "but with..." that modify previous results
    - References to "instead of" or "similarly to" previous outputs
    
    DO NOT consider these as sufficient:
    - Simply continuing an analytical theme without reference
    - Using similar tables without connecting to previous work
    - General follow-up questions that don't reference previous results
    
    Respond with a JSON object:
    {
        "requires_context": true/false,
        "relationship_type": "self-contained" | "direct_continuation" | "specific_reference" | "ordinal_reference",
        "relevant_query_id": "ID of the most relevant previous query (if any, use the ID provided in the prompt)",
        "relevant_query_index": the 1-based index of the relevant query as shown in the list,
        "confidence": 1-10 (how confident you are in this assessment),
        "explanation": "Brief explanation of your reasoning"
    }
    
    When in doubt, consider the natural flow of conversation. Phrases like "give me the same but..." 
    strongly suggest continuation from the previous query.
    
    Apply a confidence threshold of 7+ to use context from previous queries.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "CONTEXT_ANALYSIS", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "CONTEXT_ANALYSIS_RESPONSE", "", response)
    
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
        
        # Balanced confidence threshold - require confidence 7+ to apply context
        if analysis.get("confidence", 0) < 7:
            analysis["requires_context"] = False
            analysis["explanation"] += " (Confidence below threshold 7, defaulting to no context)"
        
        # Extra check - if relationship type is self-contained, ensure requires_context is False
        if analysis.get("relationship_type") == "self-contained":
            analysis["requires_context"] = False
        
        # Print detailed debug information about the decision
        if analysis.get("requires_context", False):
            relevant_id = analysis.get("relevant_query_id", "unknown")
            relevant_index = analysis.get("relevant_query_index", 0)
            
            # Find the referenced query for more context
            referenced_query = None
            if relevant_index > 0 and relevant_index <= len(past_queries):
                referenced_query = past_queries[relevant_index-1]
            elif relevant_id:
                for q in past_queries:
                    if q.get("id") == relevant_id:
                        referenced_query = q
                        break
            
            referenced_text = "unknown query"
            if referenced_query:
                referenced_text = f"'{referenced_query.get('request', '')}'"
            
            print(f"✅ USING CONTEXT from previous query")
            print(f"  - Relationship: {analysis.get('relationship_type', 'unknown')}")
            print(f"  - Referenced query: #{relevant_index} (ID: {relevant_id})")
            print(f"  - Referenced query text: {referenced_text}")
            print(f"  - Confidence: {analysis.get('confidence', 0)}/10")
            print(f"  - Explanation: {analysis.get('explanation', 'No explanation provided')}")
        else:
            print(f"❌ NOT USING context from any previous query")
            print(f"  - Relationship: {analysis.get('relationship_type', 'self-contained')}")
            print(f"  - Confidence: {analysis.get('confidence', 0)}/10")
            print(f"  - Explanation: {analysis.get('explanation', 'No explanation provided')}")
        
        print("="*80 + "\n")
        return analysis
        
    except Exception as e:
        print(f"Error parsing context analysis: {str(e)}")
        traceback.print_exc()
        print("❌ Error in context analysis - defaulting to NO context")
        print("="*80 + "\n")
        
        # Default to no context on error
        return {
            "requires_context": False,
            "relationship_type": "self-contained",
            "explanation": f"Error in context analysis: {str(e)}. Defaulting to no context."
        } 
"""
Utility functions for the LLM compiler.

This module provides general utility functions for code extraction,
logging, and other helper functions used throughout the compiler.
"""

import re
import json
from typing import List, Dict, Any, Set
from datetime import datetime

from spark_pg_agent_formal.db.schema_memory import SchemaMemory
from spark_pg_agent_formal.core.context import CompilationContext


def extract_code_from_response(response: str) -> str:
    """
    Extract code blocks from an LLM response.
    
    Args:
        response: Raw LLM response text
        
    Returns:
        Extracted code
    """
    # Try to find Python code blocks with markdown syntax
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', response, re.DOTALL)
    
    if code_blocks:
        # Return the largest code block (likely the complete implementation)
        return max(code_blocks, key=len).strip()
    
    # If no code blocks found, try to extract based on common patterns
    lines = response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            in_code = True
        
        if in_code:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines)
    
    # If all else fails, return the raw response
    return response


def extract_tables_from_text(text: str, schema_memory: SchemaMemory) -> List[str]:
    """
    Extract table names from text based on the schema.
    
    Args:
        text: Text to extract table names from
        schema_memory: Schema memory with available tables
        
    Returns:
        List of extracted table names
    """
    available_tables = schema_memory.get_all_table_names()
    mentioned_tables = []
    
    for table in available_tables:
        if table.lower() in text.lower():
            mentioned_tables.append(table)
    
    return mentioned_tables


def log_to_file(log_file: str, phase: str, prompt: str, response: str = None):
    """
    Log prompts and responses to a file.
    
    Args:
        log_file: Path to the log file
        phase: The compilation phase (schema_analysis, plan_generation, etc.)
        prompt: The prompt sent to the LLM
        response: The response from the LLM
    """
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"PHASE: {phase}\n")
        f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n\n")
        
        f.write("PROMPT:\n")
        f.write(f"{prompt}\n\n")
        
        if response:
            f.write("RESPONSE:\n")
            f.write(f"{response}\n\n")
            
        f.write(f"\n{'='*80}\n\n")


def is_request_refinement(current_request: str, previous_request: str, schema_memory: SchemaMemory) -> bool:
    """
    Determine if current request is a refinement of previous request using semantic similarity.
    
    Args:
        current_request: The current request text
        previous_request: The previous request text
        schema_memory: Schema memory for table and column information
        
    Returns:
        True if current request appears to be a refinement of previous request
    """
    # Debug logging to help diagnose issues
    print(f"Checking if '{current_request}' is a refinement of '{previous_request}'")

    # Clean and normalize requests
    current_lower = current_request.lower().strip()
    previous_lower = previous_request.lower().strip()
    
    # 1. First check: Look for explicit refinement indicators (high precision)
    refinement_starters = [
        "instead", "but", "actually", "wait", "correction", 
        "modify", "change", "update", "revise"
    ]
    
    for starter in refinement_starters:
        if current_lower.startswith(starter):
            print(f"✓ Detected explicit refinement indicator '{starter}' at start of request")
            return True
            
    # 2. Check for pronouns that might refer to previous query
    # These are strong indicators when at the start of a sentence
    pronoun_refs = ["it", "that", "this", "these", "those"]
    for pronoun in pronoun_refs:
        if current_lower.startswith(pronoun + " "):
            print(f"✓ Detected pronoun reference '{pronoun}' indicating refinement")
            return True
    
    # 3. Check if the current request is very short (likely a refinement)
    # Short requests are often refinements like "add customer name" or "sort by date"
    if len(current_lower.split()) < 5 and any(verb in current_lower for verb in ["add", "include", "show", "sort", "filter", "group", "exclude"]):
        print(f"✓ Detected short request with action verb, likely a refinement")
        return True
        
    # 4. Detect if tables from previous request are assumed without explicit mention
    # We'll need schema info for this check
    previous_tables = extract_tables_from_text(previous_request, schema_memory)
    current_tables = extract_tables_from_text(current_request, schema_memory)
    
    # If the current request doesn't specify any tables but uses column names
    # that appeared in the previous request's tables, it's likely a refinement
    if not current_tables and previous_tables:
        # Extract column references from current request
        column_refs = extract_column_references(current_request, schema_memory)
        if column_refs:
            # Check if these columns belong to the previous tables
            schema_tables = schema_memory.get_tables_info()
            for col in column_refs:
                for table in previous_tables:
                    if table in schema_tables and col in schema_tables[table]["columns"]:
                        print(f"✓ Request references column '{col}' from previous table '{table}' without specifying the table")
                        return True
    
    # 5. Check for common phrases that indicate building upon previous result
    continuation_phrases = [
        "also", "additionally", "in addition", "as well", "too",
        "furthermore", "moreover", "and", "plus", "along with"
    ]
    
    for phrase in continuation_phrases:
        if f" {phrase} " in f" {current_lower} ":
            print(f"✓ Detected continuation phrase '{phrase}' indicating building on previous result")
            return True
    
    # 6. Use semantic similarity as a last resort
    # For semantic similarity, we'd ideally use embeddings, but we'll approximate with
    # a token overlap approach that's more sophisticated than simple keyword matching
    
    # Tokenize both requests (simple approach - split by spaces and punctuation)
    import re
    def tokenize(text):
        # Convert to lowercase, replace punctuation with spaces, and split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return set(text.split())
        
    current_tokens = tokenize(current_lower)
    previous_tokens = tokenize(previous_lower)
    
    # Calculate Jaccard similarity (intersection over union)
    if current_tokens and previous_tokens:
        intersection = current_tokens.intersection(previous_tokens)
        union = current_tokens.union(previous_tokens)
        
        # Calculate similarity score
        similarity = len(intersection) / len(union) if union else 0
        
        # Define threshold - higher means more conservative matching
        # 0.3 is a reasonable threshold based on testing
        threshold = 0.3
        
        if similarity >= threshold:
            print(f"✓ Semantic similarity detected ({similarity:.2f} >= {threshold})")
            return True
            
        print(f"Semantic similarity score: {similarity:.2f} (below threshold {threshold})")
    
    print("✗ Not detected as a refinement request")
    return False


def extract_column_references(text: str, schema_memory: SchemaMemory) -> List[str]:
    """
    Extract potential column references from text.
    
    Args:
        text: The text to search for column references
        schema_memory: Schema memory for tables and columns information
        
    Returns:
        List of column names found in the text
    """
    # Get all table and column information
    schema_tables = schema_memory.get_tables_info()
    all_columns = []
    
    # Collect all column names from all tables
    for table, info in schema_tables.items():
        all_columns.extend(info.get("columns", []))
        
    # Make unique list of columns
    all_columns = list(set(all_columns))
    
    # Find columns mentioned in the text
    mentioned_columns = []
    for col in all_columns:
        # Simple matching - could be improved with word boundary checks
        if col.lower() in text.lower().split():
            mentioned_columns.append(col)
            
    return mentioned_columns


def store_transformation(request: str, code: str, context: CompilationContext, previous_transformations: List[Dict[str, Any]]):
    """
    Store transformation details for future context preservation.
    
    Args:
        request: The user request that generated the transformation
        code: The generated code
        context: The compilation context
        previous_transformations: List to store transformations in
    """
    transformation = {
        "request": request,
        "code": code,
        "tables": context.tables_referenced.copy() if context.tables_referenced else [],
        "columns": context.columns_referenced.copy() if context.columns_referenced else {},
        "timestamp": datetime.now().isoformat(),
    }
    
    # Store execution plan if available
    if context.execution_plan:
        transformation["execution_plan"] = context.execution_plan
    
    # Store final DataFrame structure if available
    if "code_review" in context.phase_results and "passed" in context.phase_results["code_review"]:
        # Extract DataFrame columns from the final code if possible
        df_structure = extract_dataframe_structure(code)
        if df_structure:
            transformation["result_structure"] = df_structure
    
    # Limit stored transformations to last 5
    previous_transformations.append(transformation)
    if len(previous_transformations) > 5:
        previous_transformations.pop(0)


def extract_dataframe_structure(code: str) -> Dict[str, Any]:
    """
    Extract the structure of the final DataFrame from code.
    
    Args:
        code: The generated PySpark code
        
    Returns:
        Dictionary with DataFrame structure information or None if unable to extract
    """
    structure = {"columns": []}
    
    # Look for columns in the final select statement
    select_pattern = r'\.select\(\s*(.*?)\s*\)'
    match = re.search(select_pattern, code, re.DOTALL)
    if match:
        select_content = match.group(1)
        
        # Extract column names and sources
        col_pattern = r'(?:F\.col\(["\'](.*?)["\']\)|["\'](.*?)["\']|\["(.*?)"\])'
        col_matches = re.finditer(col_pattern, select_content)
        
        for m in col_matches:
            col_name = m.group(1) or m.group(2) or m.group(3)
            if col_name and col_name not in structure["columns"]:
                structure["columns"].append(col_name)
    
    return structure if structure["columns"] else None 
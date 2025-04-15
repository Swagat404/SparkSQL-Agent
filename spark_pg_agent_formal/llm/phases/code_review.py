"""
Code review phase for the LLM compiler.

This module is responsible for reviewing the generated code for issues and providing fixes.
"""

from typing import Callable, Dict, Any

from spark_pg_agent_formal.core.context import CompilationContext
from spark_pg_agent_formal.llm.providers import LLMProvider


def code_review(
    context: CompilationContext,
    llm_provider: LLMProvider,
    enable_logging: bool,
    log_file: str,
    validate_and_fix_code_func: Callable
) -> CompilationContext:
    """
    Phase 4: Review the generated code for issues.
    
    Args:
        context: The compilation context
        llm_provider: The LLM provider for generating completions
        enable_logging: Whether to log prompts and responses
        log_file: Path to the log file
        validate_and_fix_code_func: Function to validate and fix common code issues
        
    Returns:
        Updated compilation context
    """
    from spark_pg_agent_formal.llm.utils.utils import extract_code_from_response, log_to_file
    
    # Update current phase
    context.current_phase = "code_review"
    
    # Get the generated code
    code = context.phase_results.get("code_generation", {}).get("code", "")
    
    # Validate and fix common code issues
    fixed_code = validate_and_fix_code_func(code)
    
    # Log the validation
    if enable_logging and fixed_code != code:
        log_to_file(log_file, "CODE_VALIDATION", code, fixed_code)
    
    # Update the code if it was fixed
    if fixed_code != code:
        context.phase_results["code_generation"]["code"] = fixed_code
        context.phase_results["code_review"] = {
            "passed": True,
            "original_code": code,
            "fixed_code": fixed_code
        }
        return context
        
    # Create prompt for code review
    prompt = f"""
    You are reviewing PySpark code for potential issues before execution.
    
    Original Request: "{context.user_request}"
    
    Generated Code:
    ```python
    {code}
    ```
    
    Please review the code for the following issues:
    1. Missing imports or required dependencies
    2. Incorrect table or column references
    3. Syntax errors in PySpark operations
    4. Potential runtime errors (e.g., accessing non-existent columns)
    5. Inefficient operations or optimization opportunities
    6. Verify that the final result is stored in 'result_df'
    
    If issues are found, provide a corrected version of the code.
    If no significant issues are found, respond with "PASS" followed by any minor suggestions.
    
    IMPORTANT: Make sure the final result is stored in a variable named 'result_df' as this will be used by the execution system.
    If you provide a corrected version, ensure it's a complete, executable Python script, not just code fragments.
    """
    
    # Log the prompt
    if enable_logging:
        log_to_file(log_file, "CODE_REVIEW", prompt)
    
    # Get response from LLM
    response = llm_provider.get_completion(prompt)
    
    # Log the response
    if enable_logging:
        log_to_file(log_file, "CODE_REVIEW_RESPONSE", "", response)
    
    # Check if review found issues
    if response.strip().startswith("PASS"):
        # No significant issues found
        context.phase_results["code_review"] = {
            "passed": True,
            "suggestions": response.replace("PASS", "").strip(),
            "original_code": code
        }
    else:
        # Issues found, extract corrected code
        corrected_code = extract_code_from_response(response)
        
        if corrected_code and len(corrected_code) > 20 and corrected_code.strip().startswith("import"):  # Ensure it's valid code, not just a short snippet
            # Use the corrected code
            fixed_corrected_code = validate_and_fix_code_func(corrected_code)
            context.phase_results["code_generation"]["code"] = fixed_corrected_code
            context.phase_results["code_review"] = {
                "passed": False,
                "issues": response,
                "original_code": code,
                "corrected_code": fixed_corrected_code
            }
        else:
            # Keep original code if no valid correction was provided
            context.phase_results["code_review"] = {
                "passed": False,
                "issues": response,
                "no_valid_correction": True
            }
    
    return context 
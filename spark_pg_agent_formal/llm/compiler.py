"""
Multi-phase LLM compiler for Spark PostgreSQL Agent.

This module implements a multi-phase approach to LLM-based code generation,
breaking down the process into discrete steps for more reliable results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
import json
import re
import uuid
import traceback
from datetime import datetime

from spark_pg_agent_formal.db.schema_memory import SchemaMemory
from spark_pg_agent_formal.llm.providers import LLMProvider
from spark_pg_agent_formal.core.types import CompilationPhase
from spark_pg_agent_formal.tracing import (
    trace_compilation_phase,
    trace_llm_call,
    disable_console_output,
    enable_console_output
)

# New imports for refactored modules
from spark_pg_agent_formal.core.context import CompilationContext
from spark_pg_agent_formal.llm.phases.schema_analysis import schema_analysis
from spark_pg_agent_formal.llm.phases.plan_generation import plan_generation
from spark_pg_agent_formal.llm.phases.code_generation import (
    standard_code_generation,
    context_aware_code_generation,
    error_aware_code_generation,
    refinement_code_generation
)
from spark_pg_agent_formal.llm.phases.code_review import code_review
from spark_pg_agent_formal.llm.utils.code_validation import validate_and_fix_code
from spark_pg_agent_formal.llm.utils.utils import (
    extract_code_from_response,
    extract_tables_from_text,
    log_to_file,
    is_request_refinement,
    store_transformation,
    extract_dataframe_structure
)


@dataclass
class CompilationContext:
    """Context for the multi-phase compilation process"""
    user_request: str
    schema_memory: SchemaMemory
    postgres_config: Dict[str, Any] = None
    tables_referenced: List[str] = field(default_factory=list)
    columns_referenced: Dict[str, List[str]] = field(default_factory=dict)
    joins: List[Dict[str, str]] = field(default_factory=list)
    execution_plan: Optional[str] = None
    code_skeleton: Optional[str] = None
    previous_error: Optional[str] = None
    current_phase: str = "init"
    phase_results: Dict[str, Any] = field(default_factory=dict)
    transformation_id: str = None
    attempt_number: int = 1
    compilation_session_id: str = field(default_factory=lambda: f"compile_{uuid.uuid4().hex[:8]}")


class MultiPhaseLLMCompiler:
    """
    Multi-phase compiler for generating PySpark code from natural language.
    
    This compiler breaks down the process into distinct phases:
    1. Schema analysis - Identify tables and columns needed
    2. Plan generation - Create a high-level execution plan
    3. Code generation - Implement the plan in PySpark code
    4. Code review - Validate the generated code against common issues
    
    Each phase builds upon the previous one, creating a more robust and reliable
    code generation process than a single-shot approach.
    """
    
    def __init__(self, llm_provider: LLMProvider, schema_memory: SchemaMemory):
        """
        Initialize the multi-phase compiler.
        
        Args:
            llm_provider: LLM provider for text generation
            schema_memory: Schema memory for database structure awareness
        """
        self.llm_provider = llm_provider
        self.schema_memory = schema_memory
        self._last_context = None  # Track the last compilation context
        self.enable_logging = True  # Enable logging by default
        self.log_file = "compiler_logs.txt"  # Default log file name
        self.previous_transformations = []  # Store previous transformation results
    
    def compile(self, request: str, postgres_config: Dict[str, Any] = None) -> str:
        """
        Compile a natural language request into PySpark code.
        
        Args:
            request: Natural language request describing the transformation
            postgres_config: Optional PostgreSQL connection configuration
            
        Returns:
            PySpark code implementing the requested transformation
        """
        # Check if this request is related to previous transformations
        is_refinement = False
        related_transformation = None
        
        if self.previous_transformations:
            last_transformation = self.previous_transformations[-1]
            is_refinement = is_request_refinement(request, last_transformation["request"], self.schema_memory)
            if is_refinement:
                related_transformation = last_transformation
        
        # Initialize compilation context
        context = CompilationContext(
            user_request=request,
            schema_memory=self.schema_memory,
            postgres_config=postgres_config
        )
        
        # Add previous transformation info if this is a refinement or related request
        if related_transformation:
            print(f"Detected related transformation: '{request}' is building on '{related_transformation['request']}'")
            context.phase_results["previous_transformation"] = related_transformation
            
            # If request appears to be an explicit refinement, mark it as such
            if is_refinement:
                print("Setting up refinement context")
                context.phase_results["refinement_context"] = {
                    "original_request": related_transformation["request"],
                    "original_code": related_transformation["code"],
                }
                if "result_summary" in related_transformation:
                    context.phase_results["original_result_summary"] = related_transformation["result_summary"]
        
        # Run the compilation process
        code = self.compile_with_context(context)
        
        # Store this transformation for future reference
        store_transformation(request, code, context, self.previous_transformations)
        
        return code
    
    def compile_with_context(self, context: CompilationContext) -> str:
        """
        Multi-phase compilation with context awareness.
        
        Args:
            context: CompilationContext object with compilation state
            
        Returns:
            Generated PySpark code
        """
        try:
            # Set up logging for this compilation session
            if self.enable_logging:
                self.log_file = f"compiler_logs_{context.compilation_session_id}.txt"
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"COMPILATION SESSION: {context.compilation_session_id}\n")
                    f.write(f"USER REQUEST: {context.user_request}\n")
                    f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n\n")
            
            print("Running phase: SCHEMA_ANALYSIS")
            # First add tracing for schema analysis with START event
            trace_compilation_phase("SCHEMA_ANALYSIS")(lambda ctx: ctx)(context, is_start=True)
            context = schema_analysis(context, self.llm_provider, self.enable_logging, self.log_file, extract_tables_from_text)
            # Add END event for schema analysis
            trace_compilation_phase("SCHEMA_ANALYSIS")(lambda ctx: ctx)(context)
            
            print("Running phase: PLAN_GENERATION")
            # First add tracing for plan generation with START event
            trace_compilation_phase("PLAN_GENERATION")(lambda ctx: ctx)(context, is_start=True)
            context = plan_generation(context, self.llm_provider, self.enable_logging, self.log_file)
            # Add END event for plan generation
            trace_compilation_phase("PLAN_GENERATION")(lambda ctx: ctx)(context)
            
            print("Running phase: CODE_GENERATION")
            # Determine which code generation phase to use
            if "refinement_context" in context.phase_results:
                # This is a refinement of a rejected transformation
                # Add tracing for refinement code generation
                trace_compilation_phase("CODE_GENERATION")(lambda ctx: ctx)(context, is_start=True)
                context = refinement_code_generation(context, self.llm_provider, self.enable_logging, self.log_file)
                trace_compilation_phase("CODE_GENERATION")(lambda ctx: ctx)(context)
            elif "previous_code" in context.phase_results:
                # This is a relative request
                # Add tracing for context-aware code generation
                trace_compilation_phase("CONTEXT_AWARE_CODE_GENERATION")(lambda ctx: ctx)(context, is_start=True)
                context = context_aware_code_generation(context, self.llm_provider, self.enable_logging, self.log_file)
                trace_compilation_phase("CONTEXT_AWARE_CODE_GENERATION")(lambda ctx: ctx)(context)
            elif "previous_errors" in context.phase_results and context.phase_results["previous_errors"]:
                # This has previous errors
                # Add tracing for error-aware code generation
                trace_compilation_phase("ERROR_AWARE_CODE_GENERATION")(lambda ctx: ctx)(context, is_start=True)
                context = error_aware_code_generation(context, self.llm_provider, self.enable_logging, self.log_file)
                trace_compilation_phase("ERROR_AWARE_CODE_GENERATION")(lambda ctx: ctx)(context)
            else:
                # Standard code generation
                # Add tracing for standard code generation
                trace_compilation_phase("CODE_GENERATION")(lambda ctx: ctx)(context, is_start=True)
                context = standard_code_generation(context, self.llm_provider, self.enable_logging, self.log_file)
                trace_compilation_phase("CODE_GENERATION")(lambda ctx: ctx)(context)
                
            print("Running phase: CODE_REVIEW")
            # Add tracing for code review
            trace_compilation_phase("CODE_REVIEW")(lambda ctx: ctx)(context, is_start=True)
            context = code_review(context, self.llm_provider, self.enable_logging, self.log_file, validate_and_fix_code)
            trace_compilation_phase("CODE_REVIEW")(lambda ctx: ctx)(context)
            
            # Store the final context for visualization purposes
            self._last_context = context
        
            # Extract the final code
            final_code = context.phase_results.get("code_generation", {}).get("code", "")
            
            # Log the final code
            if self.enable_logging:
                log_to_file(self.log_file, "FINAL_CODE", "", final_code)
            
            return final_code
            
        except Exception as e:
            print(f"Error during compilation: {str(e)}")
            traceback.print_exc()
            
            # Store error in context if available
            if context:
                context.phase_results["error"] = str(e)
                self._last_context = context
                
                # Log the error
                if self.enable_logging:
                    log_to_file(self.log_file, "ERROR", "", f"Error during compilation: {str(e)}\n{traceback.format_exc()}")
            
            raise
    
    def _extract_code_from_response(self, response: str) -> str:
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
    
    def _validate_and_fix_code(self, code: str) -> str:
        """Validate and fix common code issues."""
        if not code:
            return code
        
        # Track if we made any fixes
        fixes_made = []
        
        # First fix: Ensure correct formatting for the UNCOMMENTED version of SparkSession
        # Since the executor will modify this, we need to make sure the uncommented version is also correct
        
        # Pattern for commented SparkSession builder with continuation format
        commented_builder_pattern = re.compile(r'# spark\s*=\s*SparkSession\.builder\s*\\?\s*\n(\s*)#\s*\.', re.MULTILINE)
        
        if commented_builder_pattern.search(code):
            # Fix the commented version first
            code = re.sub(
                commented_builder_pattern,
                lambda m: '# spark = SparkSession.builder\\\n' + m.group(1) + '#     .',
                code
            )
            fixes_made.append("Fixed commented SparkSession.builder pattern")
            print("✓ Fixed commented SparkSession.builder pattern")
        
        # Pattern for the SparkSession builder with continuation format
        spark_session_pattern = re.compile(r'(spark\s*=\s*SparkSession\.builder\s*\\?\s*\n)(\s*)\.', re.MULTILINE)
        
        if spark_session_pattern.search(code):
            # Fix the uncommented version
            code = re.sub(
                spark_session_pattern,
                lambda m: m.group(1) + '    .',
                code
            )
            fixes_made.append("Fixed uncommented SparkSession.builder pattern")
            print("✓ Fixed uncommented SparkSession.builder pattern")
        
        # Create a special direct replacement for SparkSession creation to avoid indentation issues
        spark_creation_pattern = re.compile(
            r'(?:# )?spark\s*=\s*SparkSession\.builder\s*\\?.*?\.getOrCreate\(\)',
            re.DOTALL
        )
        
        if spark_creation_pattern.search(code):
            # Replace with a properly formatted standard pattern 
            # This pattern works both commented and uncommented
            standard_builder = """# spark = SparkSession.builder\\
#     .appName("PySpark Transformation")\\
#     .getOrCreate()"""
            
            code = re.sub(
                spark_creation_pattern,
                standard_builder,
                code
            )
            fixes_made.append("Standardized SparkSession builder pattern")
            print("✓ Applied standard SparkSession builder pattern")
        
        # Fix common indentation errors with multi-line SparkSession creation
        lines = code.split('\n')
        fixed_lines = []
        
        # First pass: Fix SparkSession creation blocks
        in_spark_session = False
        builder_indent = 0
        session_start_line = -1
        continuation_line = False
        
        for i, line in enumerate(lines):
            # Detect SparkSession creation patterns
            if "SparkSession.builder" in line:
                in_spark_session = True
                session_start_line = i
                builder_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                continuation_line = line.strip().endswith("\\")
                print(f"✓ Found SparkSession.builder at line {i+1}, indent level: {builder_indent}")
                continue
                
            # Fix indentation in multi-line SparkSession creation
            if in_spark_session:
                strip_line = line.strip()
                
                # If this is a continuation of the builder pattern
                if strip_line.startswith('.') or continuation_line:
                    # Apply proper indentation (builder_indent + 4 spaces)
                    if not line.startswith(" " * (builder_indent + 4)) and strip_line:
                        fixed_line = " " * (builder_indent + 4) + strip_line
                        fixed_lines.append(fixed_line)
                        fixes_made.append(f"Fixed indentation in SparkSession builder at line {i+1}")
                        print(f"✓ Fixed line {i+1}: '{line}' -> '{fixed_line}'")
                    else:
                        fixed_lines.append(line)
                
                    continuation_line = strip_line.endswith("\\")
                    
                    # Check if we're done with the SparkSession creation
                    if strip_line.endswith(".getOrCreate()") or "getOrCreate()" in strip_line:
                        in_spark_session = False
                        print(f"✓ Completed SparkSession builder block at line {i+1}")
                else:
                    # We've exited the SparkSession creation
                    in_spark_session = False
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # Second pass: Fix method chaining patterns throughout the code
        fixed_code = "\n".join(fixed_lines)
        lines = fixed_code.split('\n')
        fixed_lines = []
        
        # Track backslash continuation to maintain state between lines
        continuation_active = False
        continuation_indent = 0
        
        for i, line in enumerate(lines):
            strip_line = line.strip()
            current_indent = len(line) - len(line.lstrip())
            
            # Handle continuation from previous line
            if continuation_active and strip_line and not strip_line.startswith('#'):
                # This line should be indented to match continuation_indent
                if current_indent != continuation_indent and not strip_line.startswith('.'):
                    fixed_line = " " * continuation_indent + strip_line
                    fixed_lines.append(fixed_line)
                    fixes_made.append(f"Fixed continuation indentation at line {i+1}")
                    print(f"✓ Fixed continuation at line {i+1}: '{line}' -> '{fixed_line}'")
                else:
                    fixed_lines.append(line)
            
                # Check if continuation continues with this line
                continuation_active = strip_line.endswith("\\")
            
            # If this line starts with a dot (method chaining), it should align with previous line
            elif strip_line.startswith('.') and i > 0:
                prev_line = lines[i-1].rstrip()
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                
                if prev_line.endswith("\\"):
                    # Previous line has continuation - match its indent + 4
                    if current_indent != prev_indent + 4:
                        fixed_line = " " * (prev_indent + 4) + strip_line
                        fixed_lines.append(fixed_line)
                        fixes_made.append(f"Fixed dot-method indentation at line {i+1}")
                        print(f"✓ Fixed dot-method indent at line {i+1}: '{line}' -> '{fixed_line}'")
                    else:
                        fixed_lines.append(line)
                else:
                    # Regular method chaining - match previous indent + 4 or + 2
                    if not line.startswith(' ' * (prev_indent + 4)) and not line.startswith(' ' * (prev_indent + 2)):
                        fixed_line = ' ' * (prev_indent + 4) + strip_line
                        fixed_lines.append(fixed_line)
                        fixes_made.append(f"Fixed dot-method indentation at line {i+1}")
                        print(f"✓ Fixed method chain at line {i+1}: '{line}' -> '{fixed_line}'")
                    else:
                        fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            
            # Start tracking continuation if this line ends with backslash
            if strip_line.endswith("\\"):
                continuation_active = True
                continuation_indent = current_indent + 4
            else:
                continuation_active = False
        
        fixed_code = "\n".join(fixed_lines)
        
        # Fix common column reference patterns for joins to prevent ambiguity
        # Change: df.join(other_df, "id") -> df.join(other_df, df["id"] == other_df["id"])
        join_pattern = r'\.join\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']'
        if re.search(join_pattern, fixed_code):
            fixed_code = re.sub(
                join_pattern,
                lambda m: f'.join({m.group(1)}, F.col("{m.group(2)}") == {m.group(1)}["{m.group(2)}"]',
                fixed_code
            )
            fixes_made.append("Fixed ambiguous join conditions")
            print("✓ Fixed ambiguous join conditions")
        
        # Sometimes column references aren't qualified in where clauses, filter, etc.
        # Try to fix those by prepending "df." to ensure proper qualification
        # The regex catches common filter/where patterns with bare column references
        condition_pattern = r'(\.(filter|where)\s*\(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*(==|!=|>|<|>=|<=)'
        if re.search(condition_pattern, fixed_code):
            fixed_code = re.sub(
                condition_pattern,
                lambda m: f'{m.group(1)}F.col("{m.group(3)}") {m.group(4)}',
                fixed_code
            )
            fixes_made.append("Fixed unqualified column references in conditions")
            print("✓ Fixed unqualified column references")
        
        # Add a helper function to standardize join conditions to prevent ambiguity
        def standardize_join_conditions(match):
            full_join = match.group(0)
            df_name = match.group(1)
            other_df = match.group(2)
            on_condition = match.group(3).strip()
            
            # If the join already uses dataframe["column"] == other["column"] format, keep it
            if "==" in on_condition:
                return full_join
                
            # Strip quotes if present
            on_condition = on_condition.strip("'\"")
            
            # Simple case - single column name
            if on_condition.count(',') == 0 and not on_condition.startswith('['):
                return f"{df_name}.join({other_df}, {df_name}[\"{on_condition}\"] == {other_df}[\"{on_condition}\"])"
            
            # Multiple columns case (comma-separated)
            if ',' in on_condition:
                columns = [c.strip().strip("'\"") for c in on_condition.split(',')]
                conditions = " & ".join([f"{df_name}[\"{col}\"] == {other_df}[\"{col}\"]" for col in columns])
                return f"{df_name}.join({other_df}, {conditions})"
                
            # If it's already a complex condition, leave it unchanged
            return full_join
        
        # Fix simple join conditions to prevent ambiguous column references
        # Matches patterns like: df.join(other_df, "column_name") or df.join(other_df, ["col1", "col2"])
        join_pattern = re.compile(r'(\w+)\.join\((\w+),\s*([^)]+)\)')
        code = join_pattern.sub(standardize_join_conditions, code)
        
        # Add explicit error-pattern fixes
        # Fix ambiguous column references in join conditions
        ambiguous_ref_pattern = re.compile(r'(\w+)\.(\w+)\s*==\s*(\w+)\.(\w+)')
        def fix_ambiguous_refs(match):
            left_df, left_col, right_df, right_col = match.groups()
            return f"{left_df}[\"{left_col}\"] == {right_df}[\"{right_col}\"]"
        
        code = ambiguous_ref_pattern.sub(fix_ambiguous_refs, code)
        
        # Find dataframe alias uses and standardize column references
        # This will replace df.column with df["column"] to avoid ambiguity
        df_column_pattern = re.compile(r'(\w+)\.([a-zA-Z]\w*(?:\([^)]*\))?)')
        def replace_column_refs(match):
            df_name, col_ref = match.groups()
            
            # Skip if the column reference is actually a method call like filter, select, etc.
            spark_methods = ['join', 'select', 'filter', 'where', 'groupBy', 'agg', 'orderBy', 
                             'withColumn', 'drop', 'limit', 'count', 'show', 'head', 'take',
                             'distinct', 'dropDuplicates', 'withColumnRenamed', 'createOrReplaceTempView',
                             'collect', 'toPandas', 'printSchema', 'write', 'unionByName', 'union',
                             'intersect', 'subtract']
            
            # Don't modify method calls
            if col_ref in spark_methods or '(' in col_ref:
                return match.group(0)
                
            # Convert df.column to df["column"] syntax
            return f'{df_name}["{col_ref}"]'
            
        # Apply the column reference fix
        # Skip this fix for session objects like spark, sc, etc.
        non_df_objects = ['spark', 'sc', 'SparkSession', 'functions', 'F', 'Window', 'types', 
                          'org', 'jdbc', 'http', 'https', 'com', 'net', 'io', 'java', 'scala',
                          'postgresql', 'mysql', 'sqlserver', 'oracle', 'Driver', 'Connection']
        code_lines = code.split('\n')
        for i, line in enumerate(code_lines):
            # Skip fixing lines that mention non-dataframe objects
            if any(obj in line for obj in non_df_objects):
                continue
                
            # Skip string literals that look like JDBC URLs or package names
            if '"driver"' in line.lower() or '"url"' in line.lower() or 'import' in line.lower():
                continue
                
            # Skip lines that are inside string literals containing dots
            if ('"' in line and "." in line and line.count('"') >= 2) or \
               ("'" in line and "." in line and line.count("'") >= 2):
                continue
                
            code_lines[i] = df_column_pattern.sub(replace_column_refs, line)
        code = '\n'.join(code_lines)

        # Fix alias collisions in the code
        def fix_alias_collisions(code):
            # Track DataFrames and their aliases
            df_aliases = {}  # Maps DataFrame name to its alias
            alias_dfs = {}   # Maps alias to DataFrame name
            
            # Define patterns for alias definition and usage
            alias_def_pattern = re.compile(r'(\w+)\s+as\s+(\w+)', re.IGNORECASE)
            alias_assign_pattern = re.compile(r'(\w+)\s*=\s*(\w+)\.alias\([\'"](\w+)[\'"]\)')
            
            lines = code.split('\n')
            modified = False
            
            # First pass: collect all aliases
            for i, line in enumerate(lines):
                # Check for SQL-style aliases: df as alias
                for match in alias_def_pattern.finditer(line):
                    df_name, alias = match.groups()
                    if alias in alias_dfs and alias_dfs[alias] != df_name:
                        # Alias collision detected
                        modified = True
                        new_alias = f"{alias}_{df_name}"
                        # Replace in this line
                        lines[i] = line.replace(f"{df_name} as {alias}", f"{df_name} as {new_alias}")
                        df_aliases[df_name] = new_alias
                        alias_dfs[new_alias] = df_name
                    else:
                        df_aliases[df_name] = alias
                        alias_dfs[alias] = df_name
                
                # Check for PySpark-style aliases: new_df = df.alias("alias")
                for match in alias_assign_pattern.finditer(line):
                    new_df, orig_df, alias = match.groups()
                    if alias in alias_dfs and alias_dfs[alias] != new_df:
                        # Alias collision detected
                        modified = True
                        new_alias = f"{alias}_{new_df}"
                        # Replace in this line
                        lines[i] = line.replace(f'alias("{alias}")', f'alias("{new_alias}")')
                        df_aliases[new_df] = new_alias
                        alias_dfs[new_alias] = new_df
                    else:
                        df_aliases[new_df] = alias
                        alias_dfs[alias] = new_df
            
            # Second pass: update all alias references if we found collisions
            if modified:
                for i, line in enumerate(lines):
                    for df_name, alias in df_aliases.items():
                        # Replace references to the alias in the code
                        # This is a simplified approach - might need improvement for complex cases
                        if alias.startswith(df_name):
                            # This was a renamed alias, update references
                            old_alias = alias.split('_')[0]
                            # Replace standalone old alias with new alias (with word boundaries)
                            lines[i] = re.sub(r'\b' + old_alias + r'\b', alias, lines[i])
            
            return '\n'.join(lines)
        
        # Apply alias collision fixing
        fixed_code = fix_alias_collisions(code)
        if fixed_code != code:
            code = fixed_code
            fixes_made.append("Fixed alias collisions")
            print("✓ Fixed alias collisions")

        # Add alias uniqueness to prompt for future code generation
        def generate_prompt_with_fixes():
            return """
            # Code Quality Guidelines
            - Use explicit aliases for all DataFrame operations (e.g., df.alias("unique_name"))
            - Ensure all aliases are unique across the query
            - Use explicit join conditions with fully qualified column names:
              GOOD: df1.join(df2, df1["id"] == df2["id"])
              AVOID: df1.join(df2, "id")
            - Use bracket notation for column references:
              GOOD: df["column_name"]
              AVOID: df.column_name
            """
        
        self.code_quality_prompt = generate_prompt_with_fixes()
        
        if fixes_made:
            print(f"Code fixes applied: {', '.join(fixes_made)}")
        
        return code
    
    def _extract_tables_from_text(self, text: str, schema_memory: SchemaMemory) -> List[str]:
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
    
    def _phase_refinement_code_generation(self, context: CompilationContext) -> CompilationContext:
        """
        Generate code based on a refinement request after user rejection.
        
        Args:
            context: CompilationContext object with compilation state
            
        Returns:
            Updated CompilationContext
        """
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
        if self.enable_logging:
            log_to_file(self.log_file, "REFINEMENT_CODE_GENERATION", "", prompt)
        
        # Get response from LLM
        response = self.llm_provider.get_completion(prompt)
        
        # Log the response
        if self.enable_logging:
            log_to_file(self.log_file, "REFINEMENT_CODE_GENERATION_RESPONSE", "", response)
        
        # Extract code from the response
        code = self._extract_code_from_response(response)
        
        # Validate and fix the code before returning
        fixed_code = self._validate_and_fix_code(code)
        
        # Store generated code in context
        context.phase_results["code_generation"] = {"code": fixed_code, "full_response": response, "is_refinement": True}
        
        return context
    
    def _log_to_file(self, phase: str, prompt: str, response: str = None):
        """
        Log prompts and responses to a file.
        
        Args:
            phase: The compilation phase (schema_analysis, plan_generation, etc.)
            prompt: The prompt sent to the LLM
            response: The response from the LLM
        """
        if not self.enable_logging:
            return
            
        with open(self.log_file, "a", encoding="utf-8") as f:
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

    def _is_request_refinement(self, current_request: str, previous_request: str) -> bool:
        """Determine if current request is a refinement of previous request using semantic similarity"""
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
        previous_tables = self._extract_tables_from_text(previous_request, self.schema_memory)
        current_tables = self._extract_tables_from_text(current_request, self.schema_memory)
        
        # If the current request doesn't specify any tables but uses column names
        # that appeared in the previous request's tables, it's likely a refinement
        if not current_tables and previous_tables:
            # Extract column references from current request
            column_refs = self._extract_column_references(current_request)
            if column_refs:
                # Check if these columns belong to the previous tables
                schema_tables = self.schema_memory.get_tables_info()
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
        
    def _extract_column_references(self, text: str) -> List[str]:
        """Extract potential column references from text"""
        # Get all table and column information
        schema_tables = self.schema_memory.get_tables_info()
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

    def _store_transformation(self, request: str, code: str, context: CompilationContext):
        """Store transformation details for future context preservation"""
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
            df_structure = self._extract_dataframe_structure(code)
            if df_structure:
                transformation["result_structure"] = df_structure
        
        # Limit stored transformations to last 5
        self.previous_transformations.append(transformation)
        if len(self.previous_transformations) > 5:
            self.previous_transformations.pop(0)

    def _extract_dataframe_structure(self, code: str) -> Dict[str, Any]:
        """Extract the structure of the final DataFrame from code"""
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
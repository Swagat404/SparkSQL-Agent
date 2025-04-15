"""
Context management for compiler operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
import uuid

from spark_pg_agent_formal.db.schema_memory import SchemaMemory

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
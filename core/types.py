"""
Core types and models for the Spark PostgreSQL Agent.
"""

from enum import Enum, auto
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime


class CompilationPhase(Enum):
    """Phases of the compilation process"""
    SCHEMA_ANALYSIS = auto()
    PLAN_GENERATION = auto()
    CODE_GENERATION = auto()
    CODE_REVIEW = auto()
    EXECUTION = auto()
    VALIDATION = auto()


class AgentConfig(BaseModel):
    """Configuration for the Spark PostgreSQL Agent"""
    llm_provider: str = "openai"
    max_attempts: int = 5
    optimization_level: int = 1
    show_execution_plan: bool = True
    enable_visualization: bool = False
    validation_enabled: bool = True
    result_detection_mode: str = "enhanced"  # "strict", "lenient", "enhanced"
    result_marker_required: bool = True
    fallback_to_recent_df: bool = True


class AgentState(BaseModel):
    """State management for the Spark PostgreSQL Agent"""
    user_request: str
    phase: str = "init"
    attempt_count: int = 0
    is_valid: bool = False
    needs_confirmation: bool = False
    
    # Current compilation phase
    compilation_phase: Optional[CompilationPhase] = None
    
    # Track multi-step workflow
    workflow_step: int = 1
    workflow_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Reference to previous transformation result
    previous_result_reference: Optional[str] = None
    
    # Error tracking
    last_error: Optional[str] = None
    
    # Compilation context for tracking and visualization
    compilation_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    def update_with_new_request(self, request: str) -> None:
        """Update state with a new user request while preserving context."""
        self.user_request = request
        self.workflow_step += 1
        self.attempt_count = 0
        self.is_valid = False
        self.phase = "init"
        self.needs_confirmation = False
        self.last_error = None
        
    def increment_attempt(self) -> None:
        """Increment the attempt counter."""
        self.attempt_count += 1 
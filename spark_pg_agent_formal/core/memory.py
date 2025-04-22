"""
Memory management for the Spark PostgreSQL Agent.

This module provides context tracking and conversation memory capabilities.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import re
import uuid
from collections import Counter

# Try to import nltk modules but provide fallbacks if not available
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    
    # Try to download necessary data if not already present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            NLTK_AVAILABLE = False
            
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            NLTK_AVAILABLE = False
except ImportError:
    NLTK_AVAILABLE = False


class AgentMemory(BaseModel):
    """Memory system for tracking context across transformation steps"""
    
    # Short-term context for current session
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Track entities and their relationships across steps
    entity_tracker: Dict[str, Set[str]] = Field(default_factory=dict)
    
    # Previous transformations and results
    previous_transformations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Schema understanding that evolves during conversation
    schema_understanding: Dict[str, Any] = Field(default_factory=dict)
    
    # Track user's focus and implied intentions - maintained for compatibility
    focus_entities: List[str] = Field(default_factory=list)
    
    # Refinement context for handling rejected transformations
    refinement_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Session identifier
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Enhanced transformation tracking
    transformation_steps: Dict[int, Dict[str, Any]] = Field(default_factory=dict)
    step_counter: int = 1
    
    # Map specific references to step indices
    named_references: Dict[str, int] = Field(default_factory=dict)
    
    def __init__(self, **data):
        """Initialize agent memory"""
        super().__init__(**data)
    
    def remember_transformation(self, request: str, code: str, tables_used: List[str], 
                              columns_used: Dict[str, List[str]], result_summary: Dict[str, Any]) -> int:
        """
        Store transformation context for future reference
        
        Args:
            request: The original user request
            code: The generated code
            tables_used: List of tables used in the transformation
            columns_used: Dictionary mapping tables to their columns used
            result_summary: Summary of the transformation result
            
        Returns:
            Current step number
        """
        # Create transformation record 
        transformation = {
            "request": request,
            "code": code,
            "tables_used": tables_used,
            "columns_used": columns_used,
            "result_summary": result_summary,
            "timestamp": datetime.now().isoformat(),
            "step_number": self.step_counter,
            "id": f"query_{self.step_counter}"  # Add ID for schema_analysis.py to reference
        }
        
        # Store in previous transformations list
        self.previous_transformations.append(transformation)
        
        # Also store in indexed dictionary
        self.transformation_steps[self.step_counter] = transformation
        
        # Add to conversation history with step number
        self.conversation_history.append({
            "role": "user",
            "content": request,
            "step": self.step_counter
        })
        
        # Update focus entities based on current request
        self._update_focus_entities(request, tables_used)
        
        # Increment step counter for next transformation
        current_step = self.step_counter
        self.step_counter += 1
        
        # Create basic reference markers for this step
        self._create_reference_markers(request, current_step)
        
        return current_step
    
    def get_relevant_context(self, request: str = None) -> Dict[str, Any]:
        """
        Create a consolidated view of the conversation context for schema_analysis.py.
        Only includes the minimum necessary information to reduce token usage.
        
        Args:
            request: Optional current request for context-aware retrieval
            
        Returns:
            Dict containing context information for LLM analysis
        """
        # We only need to return a basic context here as schema_analysis.py
        # will call find_related_transformation to get the detailed history
        context = {
            "current_step": self.step_counter - 1 if self.step_counter > 1 else 0
        }
        
        return context
    
    def _update_focus_entities(self, request: str, tables_used: List[str]) -> None:
        """
        Update focus entities based on the current request and tables used.
        Maintained for compatibility, but primary context analysis is done by schema_analysis.py
        
        Args:
            request: The user request
            tables_used: Tables used in the transformation
        """
        # Simple implementation - just add tables to focus entities
        for table in tables_used:
            if table not in self.focus_entities:
                self.focus_entities.append(table)
                
        # Keep only the 5 most recent entities
        if len(self.focus_entities) > 5:
            self.focus_entities = self.focus_entities[-5:]
    
    def _extract_intentions(self) -> List[str]:
        """
        Extract basic query intentions from conversation history.
        More sophisticated intention analysis is handled by the LLM in schema_analysis.py.
        
        Returns:
            List of basic query intentions
        """
        # Simplified implementation - detect only basic SQL operations
        intentions = []
        
        # Check if we have recent transformations
        if len(self.previous_transformations) >= 1:
            # Analyze current request for basic SQL operation patterns
            curr = self.previous_transformations[-1]["request"].lower()
            
            # Detect basic SQL operations
            sql_operations = {
                "aggregation": ["aggregate", "group", "sum", "avg", "count", "min", "max"],
                "joining": ["join", "combine", "merge", "related"],
                "filtering": ["filter", "where", "having", "condition"],
                "sorting": ["sort", "order", "rank", "top"]
            }
            
            # Check for each operation type
            for intent, keywords in sql_operations.items():
                if any(keyword in curr for keyword in keywords):
                    intentions.append(intent)
                
        return intentions
        
    def add_to_conversation(self, role: str, content: str) -> None:
        """
        Add an entry to the conversation history.
        
        Args:
            role: The role (user/system/assistant)
            content: The message content
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "step": self.step_counter - 1 if self.step_counter > 1 else 0
        })
    
    def set_refinement_context(self, request, code, result):
        """
        Set the refinement context when a user rejects a transformation.
        
        Args:
            request: The original request
            code: The code that was rejected
            result: The result that was rejected
        """
        self.refinement_context = {
            "active": True,
            "original_request": request,
            "original_code": code,
            "original_result": result
        }
    
    def clear_refinement_context(self):
        """Clear the refinement context"""
        self.refinement_context = {
            "active": False,
            "original_request": None,
            "original_code": None,
            "original_result": None
        }
    
    def is_refinement_active(self):
        """Check if we're in refinement mode"""
        return self.refinement_context.get("active", False)
    
    def _create_reference_markers(self, request: str, step_number: int) -> None:
        """
        Create basic reference markers for retrieving steps later.
        Provides minimal indexing - detailed analysis is done by schema_analysis.py
        
        Args:
            request: The user request
            step_number: The step number
        """
        # Always store step by its ordinal reference
        self.named_references[f"step_{step_number}"] = step_number
        
        # First query special case
        if step_number == 1:
            self.named_references["first_query"] = step_number
            self.named_references["initial_request"] = step_number
        
        # Extract key concepts for this step - simplified to avoid domain-specific hardcoding
        concepts = self._extract_key_concepts(request)
        for concept in concepts:
            # Store generic concept references
            self.named_references[f"{concept}_step"] = step_number
            
        # Basic pattern detection for group by queries
        if "group" in request.lower() and "by" in request.lower():
            self.named_references["grouped_query"] = step_number
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text using basic NLP techniques.
        Domain-specific concept extraction is handled by the LLM in schema_analysis.py.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key concepts
        """
        # Convert to lowercase
        text = text.lower()
        
        # Extract nouns and noun phrases - simplified approach
        keywords = []
        
        # Try using nltk for better concept extraction if available
        if 'NLTK_AVAILABLE' in globals() and NLTK_AVAILABLE:
            try:
                # Tokenize and remove stopwords
                tokens = word_tokenize(text)
                stop_words = set(stopwords.words('english'))
                filtered_tokens = [w for w in tokens if w.isalnum() and w not in stop_words]
                
                # Get word frequencies and add top keywords
                word_freq = Counter(filtered_tokens)
                keywords.extend([word for word, _ in word_freq.most_common(5)])
            except Exception:
                # Fallback to simple extraction if nltk processing fails
                pass
        
        # Basic extraction of common terms in queries
        common_query_terms = ["select", "from", "where", "group", "order", "by", "having", "join", 
                            "analysis", "report", "list", "summary", "total", "count", "average", "sum"]
        
        # Simple pattern matching for generic SQL-related concepts
        generic_patterns = [
            r'(\w+) by (\w+)',
            r'(\w+) with (\w+)',
            r'top (\d+)',
            r'average (\w+)',
            r'total (\w+)',
            r'count (\w+)'
        ]
        
        # Apply generic patterns
        for pattern in generic_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for term in match:
                        if term not in keywords and term not in common_query_terms:
                            keywords.append(term)
                elif match not in keywords and match not in common_query_terms:
                    keywords.append(match)
        
        # Make sure we have unique terms
        return list(set(keywords))
    
    def get_step(self, step_reference: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific step by reference.
        References can be numerical ("step 2") or semantic ("first query")
        
        Args:
            step_reference: Reference to the step
            
        Returns:
            Dictionary containing the step transformation
        """
        # Check for direct numerical reference
        step_match = re.search(r'step (\d+)', step_reference.lower())
        if step_match:
            step_num = int(step_match.group(1))
            return self.transformation_steps.get(step_num)
        
        # Check for ordinal references
        ordinal_map = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "last": max(self.transformation_steps.keys()) if self.transformation_steps else None,
            "previous": self.step_counter - 2 if self.step_counter > 1 else None,
            "current": self.step_counter - 1 if self.step_counter > 0 else None
        }
        
        for ordinal, step_num in ordinal_map.items():
            if ordinal in step_reference.lower() and step_num:
                return self.transformation_steps.get(step_num)
        
        # Check for semantic references
        for ref_name, step_num in self.named_references.items():
            # Look for specific named references
            if ref_name.replace("_", " ") in step_reference.lower():
                return self.transformation_steps.get(step_num)
        
        # Check for approximate concept matches
        key_concepts = self._extract_key_concepts(step_reference)
        for concept in key_concepts:
            for ref_name, step_num in self.named_references.items():
                if concept in ref_name:
                    return self.transformation_steps.get(step_num)
        
        # If no specific reference found, default to most recent
        return self.transformation_steps.get(self.step_counter - 1) if self.transformation_steps else None
    
    def get_past_queries(self, max_queries: int = 5) -> List[Dict[str, Any]]:
        """
        Get a simple list of past query prompts for context analysis.
        Token-efficient method that just returns minimal info about past queries.
        
        Args:
            max_queries: Maximum number of past queries to return
            
        Returns:
            List of past queries with minimal info
        """
        past_queries = []
        if self.transformation_steps:
            # Get the keys (step numbers) in descending order (most recent first)
            recent_keys = sorted(self.transformation_steps.keys(), reverse=True)[:max_queries]
            
            # Get just the basic info needed for context determination
            for key in recent_keys:
                transformation = self.transformation_steps[key]
                if transformation:
                    past_queries.append({
                        "id": f"query_{key}",
                        "request": transformation.get("request", ""),
                        "step_number": key
                    })
        
        return past_queries

    def get_transformation_details(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific transformation by ID.
        Only called after relevance is determined.
        
        Args:
            query_id: ID of the transformation to retrieve (e.g., "query_1")
            
        Returns:
            Detailed information about the specific transformation
        """
        if not query_id.startswith("query_"):
            return None
            
        try:
            step_number = int(query_id.replace("query_", ""))
            transformation = self.transformation_steps.get(step_number)
            
            if transformation:
                return {
                    "id": query_id,
                    "request": transformation.get("request", ""),
                    "tables_used": transformation.get("tables_used", []),
                    "columns_used": transformation.get("columns_used", {}),
                    "result_summary": {
                        "row_count": transformation.get("result_summary", {}).get("row_count", "unknown"),
                        "columns": transformation.get("result_summary", {}).get("columns", []),
                        "sample_data": transformation.get("result_summary", {}).get("sample_data", [])[:2] if "sample_data" in transformation.get("result_summary", {}) else []
                    }
                }
        except ValueError:
            return None
            
        return None

    def find_related_transformation(self, current_request: str) -> Optional[Dict[str, Any]]:
        """
        Get transformation history for LLM to analyze relationships.
        Provides only the essential information needed by schema_analysis.py.
        Now just returns a list of past prompts for more token-efficient analysis.
        
        Args:
            current_request: The current user request
            
        Returns:
            Transformation history for the context's phase_results
        """
        # Get past queries with minimal information
        past_queries = self.get_past_queries(max_queries=5)
        
        # Return the list of past queries for initial relevance determination
        return {"past_queries": past_queries} if past_queries else None 
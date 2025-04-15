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
    
    # Track user's focus and implied intentions
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
            "step_number": self.step_counter
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
        
        # Create reference markers for this step
        self._create_reference_markers(request, current_step)
        
        return current_step
    
    def get_relevant_context(self, request: str = None) -> Dict[str, Any]:
        """
        Create a consolidated view of the conversation context.
        
        Args:
            request: Optional current request for context-aware retrieval
            
        Returns:
            Dict containing entity focus, recent transformations, and implied intentions
        """
        context = {
            "entity_focus": self.focus_entities,
            "recent_transformations": self.previous_transformations[-3:] if self.previous_transformations else [],
            "implied_intentions": self._extract_intentions()
        }
        
        # If a specific request is provided, enhance the context with request-specific info
        if request and self.previous_transformations:
            # Check for explicit step references
            related_transformation = self.find_related_transformation(request)
            if related_transformation and related_transformation.get("type") == "explicit_reference":
                context["referenced_transformation"] = related_transformation.get("base_transformation")
                context["reference_type"] = related_transformation.get("reference_type")
            else:
                # Analyze the request for indicators of what previous context might be relevant
                request_lower = request.lower()
                
                # Check for specific mentions of tables or entities
                for entity in self.focus_entities:
                    if entity.lower() in request_lower:
                        context["referenced_entity"] = entity
                        # Find transformations related to this entity
                        related_transformations = [
                            t for t in self.previous_transformations 
                            if entity in t.get("tables_used", [])
                        ]
                        if related_transformations:
                            context["entity_related_transformations"] = related_transformations[-1:]
                
                # Check for filtering or modification language 
                filter_terms = ["filter", "only", "where", "just", "from", "limit to"]
                for term in filter_terms:
                    if term in request_lower:
                        context["filter_requested"] = True
                        # Likely modifying previous results
                        if self.previous_transformations:
                            context["last_transformation"] = self.previous_transformations[-1]
                
                # Check for comparison language
                comparison_terms = ["more than", "greater", "less than", "higher", "lower", "top", "bottom"]
                for term in comparison_terms:
                    if term in request_lower:
                        context["comparison_requested"] = True
                
                # Extract potential condition values
                # Example: "from US" → extract "US" as a potential filter value
                country_pattern = r'\b(from|in|where|only|just)\s+([A-Z]{2})\b'
                country_match = re.search(country_pattern, request)
                if country_match:
                    context["potential_filter_value"] = country_match.group(2)
                    context["filter_type"] = "country"
        
        return context
    
    def _update_focus_entities(self, request: str, tables_used: List[str]) -> None:
        """
        Update focus entities based on the current request and tables used.
        
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
        Extract implied intentions from conversation history.
        
        Returns:
            List of implied intentions
        """
        # Simplified implementation - this could be enhanced with LLM-based analysis
        intentions = []
        
        # Check recent transformations for patterns
        if len(self.previous_transformations) >= 2:
            # Check for iteration pattern (similar requests)
            prev = self.previous_transformations[-2]["request"].lower()
            curr = self.previous_transformations[-1]["request"].lower()
            
            if "aggregate" in curr or "group" in curr:
                intentions.append("aggregation")
            if "join" in curr:
                intentions.append("joining_data")
            if "filter" in curr or "where" in curr:
                intentions.append("filtering_data")
            if "sort" in curr or "order" in curr:
                intentions.append("sorting_results")
                
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
        Create semantic markers for retrieving steps later.
        
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
        
        # Extract key concepts for this step
        concepts = self._extract_key_concepts(request)
        for concept in concepts:
            # Store specific concepts like "customer list", "revenue report"
            self.named_references[f"{concept}_step"] = step_number
            
            # For important concepts, also store ordinal variants
            if concept in ["customer", "revenue", "sales", "product"]:
                self.named_references[f"{concept}_analysis"] = step_number
                
        # Store by query type
        if "top" in request.lower() and any(term in request.lower() for term in ["customer", "spending"]):
            self.named_references["top_customers"] = step_number
            
        elif "group" in request.lower() and "by" in request.lower():
            group_by_match = re.search(r'group by (\w+)', request.lower())
            if group_by_match:
                group_by_field = group_by_match.group(1)
                self.named_references[f"grouped_by_{group_by_field}"] = step_number
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of key concepts
        """
        # Convert to lowercase
        text = text.lower()
        
        # Extract nouns and noun phrases
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
        
        # Simple extraction of nouns based on common data analysis terms
        data_terms = ["customers", "customer", "sales", "revenue", "products", "product", 
                    "orders", "order", "transactions", "users", "user", "accounts", 
                    "items", "countries", "regions", "categories", "dates", "year", 
                    "month", "day", "report", "summary", "analysis", "list", "total"]
        
        # Check for these terms in the text
        for term in data_terms:
            if term in text:
                keywords.append(term)
        
        # Check for noun phrases with simple pattern matching
        noun_phrase_patterns = [
            r'(\w+) report',
            r'(\w+) list',
            r'(\w+) analysis',
            r'(\w+) summary',
            r'(\w+) by (\w+)',
            r'top (\w+)',
            r'(\w+) statistics',
            r'(\w+) metrics',
            r'(\w+) trends',
            r'(\w+) data'
        ]
        
        for pattern in noun_phrase_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for term in match:
                        if term not in keywords:
                            keywords.append(term)
                elif match not in keywords:
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
    
    def find_related_transformation(self, current_request: str) -> Optional[Dict[str, Any]]:
        """
        Find transformations from memory that are relevant to the current request.
        
        Args:
            current_request: The current user request
            
        Returns:
            Dictionary with relevant transformation information
        """
        # First, check for explicit step references
        step_reference_patterns = [
            r"(?:go back to|use|from|in) (?:the )?(first|second|third|last|previous) (?:query|step|request)",
            r"(?:use|show|get) (?:the )?(.*?) (?:from|in) step (\d+)",
            r"(?:go to|use) step (\d+)",
            r"(?:the )?(.*?) (?:we saw|I got|you showed) earlier",
            r"(?:back to|return to) (?:the )?(.*?) (?:analysis|query|list|report)"
        ]
        
        for pattern in step_reference_patterns:
            match = re.search(pattern, current_request, re.IGNORECASE)
            if match:
                # Extract the step reference
                if len(match.groups()) == 1:
                    step_reference = match.group(1)
                else:
                    # If we captured a concept and a step, combine them
                    concept = match.group(1) if len(match.groups()) > 1 else ""
                    step_num = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    step_reference = f"{concept} step {step_num}"
                    
                # Get the referenced step
                referenced_step = self.get_step(step_reference)
                if referenced_step:
                    return {
                        "type": "explicit_reference",
                        "base_transformation": referenced_step,
                        "reference_type": step_reference
                    }
        
        # Check for "same but" type references (referring to most recent)
        same_but_patterns = [
            r"(?:the )?same (?:but|except)",
            r"(?:show|get) (?:me )?(?:the )?same",
            r"(?:like|as) (?:before|the previous|the last)",
            r"(?:similar to|just like) (?:before|the previous|the last)"
        ]
        
        for pattern in same_but_patterns:
            if re.search(pattern, current_request, re.IGNORECASE):
                if self.transformation_steps and self.step_counter > 1:
                    return {
                        "type": "relative_reference",
                        "base_transformation": self.transformation_steps.get(self.step_counter - 1),
                        "reference_type": "most_recent"
                    }
        
        # Check for entity-based references
        request_lower = current_request.lower()
        for entity in self.focus_entities:
            if entity.lower() in request_lower:
                # Find most recent transformation that used this entity
                for step in range(self.step_counter - 1, 0, -1):
                    transformation = self.transformation_steps.get(step)
                    if transformation and entity in transformation.get("tables_used", []):
                        return {
                            "type": "entity_reference",
                            "base_transformation": transformation,
                            "reference_type": f"entity_{entity}"
                        }
        
        # If no explicit reference is found, default to most recent transformation
        if self.transformation_steps and self.step_counter > 1:
            return {
                "type": "default_reference",
                "base_transformation": self.transformation_steps.get(self.step_counter - 1),
                "reference_type": "default_most_recent"
            }
        
        return None 
"""
Phase Tracker for Spark PostgreSQL Agent.

This module provides utilities for tracking and managing compilation phases in real-time,
allowing UI components to display the agent's thinking process.
"""
import json
import time
import sys
from typing import Dict, List, Optional, Any, Set, Callable
from threading import Lock

# Define a local print function instead of importing trace_print from tracer.py
def local_print(*args, **kwargs):
    """Local print function to avoid circular imports with tracer.py"""
    print(*args, **kwargs)

# Define compilation phases with their display names and order
COMPILATION_PHASES = [
    "schema_analysis", 
    "query_planning",
    "code_generation",
    "code_review",
    "executing_query"
]

PHASE_DISPLAY_NAMES = {
    "schema_analysis": "Schema Analysis",
    "query_planning": "Query Planning",
    "code_generation": "Code Generation",
    "code_review": "Code Review",
    "executing_query": "Executing Query"
}

class PhaseTracker:
    """
    Tracks compilation phases and their associated thinking processes in real-time.
    Provides callbacks for UI updates.
    """
    
    def __init__(self):
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ui_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
    def _handle_trace_event(self, event_data: Dict[str, Any]) -> None:
        """Process a trace event and update phase information"""
        session_id = event_data.get('session_id')
        if not session_id:
            return
            
        tags = event_data.get('tags', [])
        
        # Identify phase-related events
        phase_name = None
        for tag in tags:
            if tag in COMPILATION_PHASES:
                phase_name = tag
                break
                
        # If not found in standardized phases, check for variations
        if not phase_name:
            for tag in tags:
                tag_lower = tag.lower()
                if 'schema' in tag_lower and 'analysis' in tag_lower:
                    phase_name = 'schema_analysis'
                    break
                elif 'plan' in tag_lower or 'planning' in tag_lower:
                    phase_name = 'query_planning'
                    break
                elif 'code' in tag_lower and 'gen' in tag_lower:
                    phase_name = 'code_generation'
                    break
                elif 'review' in tag_lower:
                    phase_name = 'code_review'
                    break
                elif 'execut' in tag_lower:
                    phase_name = 'executing_query'
                    break
        
        if not phase_name:
            return
            
        with self._lock:
            # Initialize session data if needed
            if session_id not in self._active_sessions:
                self._active_sessions[session_id] = {
                    'phases': {phase: {'status': 'pending', 'thinking': []} for phase in COMPILATION_PHASES},
                    'current_phase': None,
                    'start_time': time.time(),
                    'last_update': time.time()
                }
            
            session_data = self._active_sessions[session_id]
            
            # Update phase information
            if 'phase_start' in tags:
                session_data['current_phase'] = phase_name
                session_data['phases'][phase_name]['status'] = 'in_progress'
                session_data['phases'][phase_name]['start_time'] = time.time()
                local_print(f"Phase started: {phase_name} for session {session_id}")
            
            elif 'phase_end' in tags:
                if phase_name == session_data.get('current_phase'):
                    session_data['current_phase'] = None
                session_data['phases'][phase_name]['status'] = 'completed'
                session_data['phases'][phase_name]['end_time'] = time.time()
                local_print(f"Phase completed: {phase_name} for session {session_id}")
            
            # Extract thinking process
            thinking = event_data.get('thinking')
            if thinking and isinstance(thinking, str):
                session_data['phases'][phase_name]['thinking'].append({
                    'timestamp': time.time(),
                    'content': thinking
                })
                local_print(f"Added thinking for phase {phase_name}: {thinking[:50]}...")
            
            # Update last_update timestamp
            session_data['last_update'] = time.time()
            
            # Trigger callbacks
            self._notify_callbacks(session_id, session_data)
    
    def _notify_callbacks(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Notify all registered callbacks about phase updates"""
        for callback in self._ui_callbacks:
            try:
                callback(session_id, session_data.copy())
            except Exception as e:
                local_print(f"Error in phase tracker callback: {str(e)}")
    
    def register_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback for receiving phase updates"""
        if callback not in self._ui_callbacks:
            self._ui_callbacks.append(callback)
            local_print(f"Registered new phase tracker callback, total: {len(self._ui_callbacks)}")
    
    def unregister_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Unregister a callback"""
        if callback in self._ui_callbacks:
            self._ui_callbacks.remove(callback)
            local_print(f"Unregistered phase tracker callback, remaining: {len(self._ui_callbacks)}")
    
    def get_session_phases(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current phase data for a session"""
        with self._lock:
            return self._active_sessions.get(session_id, {}).copy()
    
    def get_formatted_phases(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get a formatted list of phases with their status and thinking content,
        suitable for frontend display.
        """
        with self._lock:
            session_data = self._active_sessions.get(session_id)
            if not session_data:
                return []
            
            result = []
            for phase_name in COMPILATION_PHASES:
                phase_data = session_data['phases'].get(phase_name, {})
                
                # Get thinking content with proper formatting
                thinking_items = phase_data.get('thinking', [])
                thinking_content = ""
                
                if thinking_items:
                    # Join all thinking items with newlines between them
                    thinking_content = "\n\n".join([item['content'] for item in thinking_items])
                
                # Format the phase data for UI consumption
                formatted_phase = {
                    'id': phase_name,
                    'name': PHASE_DISPLAY_NAMES.get(phase_name, phase_name),
                    'status': phase_data.get('status', 'pending'),
                    'thinking': thinking_content,
                    'order': COMPILATION_PHASES.index(phase_name)
                }
                result.append(formatted_phase)
            
            return sorted(result, key=lambda x: x['order'])

    def reset_session(self, session_id: str) -> None:
        """Reset the phase tracking for a session"""
        with self._lock:
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
                local_print(f"Reset phase tracking for session {session_id}")

# Create a singleton instance of the phase tracker
phase_tracker = PhaseTracker() 
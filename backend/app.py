from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Set
import os
import sys
import json
import time
import uuid
from datetime import datetime
import asyncio
from asyncio import Queue
import traceback

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import the TransformationAgent
from spark_pg_agent_formal.core.agent import TransformationAgent
from spark_pg_agent_formal.core.types import AgentConfig, AgentState
from spark_pg_agent_formal.tracing import disable_console_output
from spark_pg_agent_formal.db.schema_memory import SchemaMemory
from spark_pg_agent_formal.execution.executor import ExecutionResult

# Import phase tracker components safely
try:
    from spark_pg_agent_formal.phase_tracker import phase_tracker, COMPILATION_PHASES, PHASE_DISPLAY_NAMES
    print(f"Imported phase_tracker: {phase_tracker}")
except ImportError as e:
    print(f"Error importing phase_tracker: {e}")
    
    # Create fallback definitions
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
    
    # Create a dummy phase tracker for testing
    class DummyPhaseTracker:
        def get_formatted_phases(self, session_id):
            return []
            
        def register_callback(self, callback):
            pass
            
        def _handle_trace_event(self, event_data):
            pass
    
    phase_tracker = DummyPhaseTracker()

# Add methods to SchemaMemory class to make it compatible with the agent
def format_schema_for_prompt(self):
    """
    Format schema information for inclusion in a prompt.
    Returns:
        Formatted schema information string
    """
    return self.get_schema_summary()

def get_schema_summary(self):
    """
    Get a summary of the schema for prompts.
    Returns:
        String with schema information
    """
    schema_text = []
    try:
        for table_name in self.tables:
            table_schema = self.tables[table_name]
            schema_text.append(f"Table: {table_name}")
            
            # Handle different column formats
            column_names = []
            
            if hasattr(table_schema, 'columns'):
                columns = table_schema.columns
                if isinstance(columns, list):
                    if len(columns) > 0:
                        if isinstance(columns[0], str):
                            column_names = columns
                        else:
                            # Try to extract name attribute from objects
                            try:
                                column_names = [getattr(col, 'name', str(col)) for col in columns]
                            except Exception as e:
                                column_names = [str(col) for col in columns]
                elif isinstance(columns, dict):
                    # If columns is a dictionary
                    column_names = list(columns.values())
                else:
                    # Other types
                    column_names = [str(columns)]
            elif isinstance(table_schema, dict):
                # If table_schema is a dictionary
                if 'columns' in table_schema:
                    cols = table_schema['columns']
                    if isinstance(cols, list):
                        if len(cols) > 0:
                            if isinstance(cols[0], dict) and 'name' in cols[0]:
                                column_names = [col['name'] for col in cols]
                            else:
                                column_names = [str(col) for col in cols]
                    elif isinstance(cols, dict):
                        column_names = list(cols.values())
                    else:
                        column_names = [str(cols)]
            
            # If we still don't have column names, use a fallback
            if not column_names:
                column_names = ["Unknown column structure"]
            
            schema_text.append(f"Columns: {', '.join(column_names)}")
            schema_text.append("")
    except Exception as e:
        schema_text.append(f"Error generating schema summary: {str(e)}")
    
    return "\n".join(schema_text)

def get_all_table_names(self):
    """
    Get all table names in the schema.
    Returns:
        List of table names
    """
    return list(self.tables.keys())

def get_column_names(self, table_name):
    """
    Get column names for a specific table.
    Args:
        table_name: Name of the table
    Returns:
        List of column names
    """
    try:
        if table_name in self.tables:
            table_schema = self.tables[table_name]
            
            # Handle different column formats
            if hasattr(table_schema, 'columns'):
                columns = table_schema.columns
                if isinstance(columns, list):
                    if len(columns) > 0:
                        if isinstance(columns[0], str):
                            return columns
                        else:
                            # Try to extract name attribute from objects
                            try:
                                return [getattr(col, 'name', str(col)) for col in columns]
                            except Exception as e:
                                return [str(col) for col in columns]
                elif isinstance(columns, dict):
                    # If columns is a dictionary
                    return list(columns.values())
                else:
                    # Other types
                    return [str(columns)]
            elif isinstance(table_schema, dict):
                # If table_schema is a dictionary
                if 'columns' in table_schema:
                    cols = table_schema['columns']
                    if isinstance(cols, list):
                        if len(cols) > 0:
                            if isinstance(cols[0], dict) and 'name' in cols[0]:
                                return [col['name'] for col in cols]
                            else:
                                return [str(col) for col in cols]
                    elif isinstance(cols, dict):
                        return list(cols.values())
                    else:
                        return [str(cols)]
            
            # If we still don't have column names, use a fallback
            return ["Unknown column structure"]
    except Exception as e:
        logger.error(f"Error getting column names: {str(e)}")
        return [f"Error: {str(e)}"]
        
    return []

def get_table_schema(self, table_name):
    """
    Get schema for a specific table.
    Args:
        table_name: Name of the table
    Returns:
        Table schema object
    """
    return self.tables.get(table_name)

# Monkey patch the SchemaMemory class
SchemaMemory.format_schema_for_prompt = format_schema_for_prompt
SchemaMemory.get_schema_summary = get_schema_summary
SchemaMemory.get_all_table_names = get_all_table_names
SchemaMemory.get_column_names = get_column_names
SchemaMemory.get_table_schema = get_table_schema

# Configure basic logging
import logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup path for spark_pg_agent imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
CONNECTIONS_FILE = os.path.join(ROOT_DIR, "connections.json")

# Disable console output from agent's tracing for API use
disable_console_output()
os.environ["SPARK_PG_AGENT_QUIET_TRACING"] = "1"
os.environ["SPARK_PG_AGENT_NO_SPINNER"] = "1"
os.environ["AGENTTRACE_NO_SPINNER"] = "1"

# Initialize FastAPI
app = FastAPI(title="SparkSQL Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Requested-With", "Accept", "Origin", "Authorization"]
)

# Database connections storage
DB_CONNECTIONS = {}

# Agent instances cache (for reuse)
AGENT_INSTANCES = {}

# Models
class DatabaseConnection(BaseModel):
    name: str
    type: str
    host: str
    port: int
    database: str
    username: str
    password: Optional[str] = None

class Query(BaseModel):
    query: str
    connection_id: str

# Helper functions
def load_connections():
    """Load database connections from file"""
    global DB_CONNECTIONS
    try:
        if os.path.exists(CONNECTIONS_FILE):
            with open(CONNECTIONS_FILE, 'r') as f:
                loaded_connections = json.load(f)
                if isinstance(loaded_connections, dict):
                    DB_CONNECTIONS = loaded_connections
                    logger.info(f"Loaded {len(DB_CONNECTIONS)} connections from {CONNECTIONS_FILE}")
                else:
                    logger.warning(f"Invalid connections file format. Expected dict, got {type(loaded_connections)}")
                    DB_CONNECTIONS = {}
        else:
            logger.info(f"Connections file not found at {CONNECTIONS_FILE}. Creating empty connections dictionary.")
            # Create an empty connections file
            save_connections()
    except Exception as e:
        logger.error(f"Error loading connections: {str(e)}")
        DB_CONNECTIONS = {}

def save_connections():
    """Save database connections to file"""
    try:
        # Ensure the directory exists
        connections_dir = os.path.dirname(CONNECTIONS_FILE)
        if not os.path.exists(connections_dir):
            os.makedirs(connections_dir)
            logger.info(f"Created directory: {connections_dir}")
            
        with open(CONNECTIONS_FILE, 'w') as f:
            json.dump(DB_CONNECTIONS, f, indent=2)
            logger.info(f"Saved {len(DB_CONNECTIONS)} connections to {CONNECTIONS_FILE}")
    except Exception as e:
        logger.error(f"Error saving connections to {CONNECTIONS_FILE}: {str(e)}")

def get_or_create_agent(connection_id):
    """Get or create a TransformationAgent for a connection"""
    # Try to get from cache first
    if connection_id in AGENT_INSTANCES:
        logger.info(f"Using cached agent for connection {connection_id}")
        return AGENT_INSTANCES[connection_id]
    
    # Get the connection details
    connection_details = DB_CONNECTIONS[connection_id]
    
    # Create postgres config from connection details
    postgres_config = {
        "host": connection_details["host"],
        "port": connection_details["port"],
        "database": connection_details["database"],
        "user": connection_details["username"],
        "password": connection_details["password"]
    }
    
    # Initialize agent config (similar to CLI)
    agent_config = AgentConfig(
        llm_provider="openai",
        max_attempts=3,
        optimization_level=1,
        show_execution_plan=True,
        enable_visualization=False,
        validation_enabled=True
    )
    
    # Create agent
    logger.info(f"Creating new agent for connection {connection_id}")
    try:
        agent = TransformationAgent(
            postgres_config=postgres_config,
            config=agent_config
        )
        
        # Cache the agent
        AGENT_INSTANCES[connection_id] = agent
        return agent
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")

# Add websocket support for real-time phase updates
class PhaseSubscription:
    """Manages subscriptions to phase updates"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new websocket client to the subscription system"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
            
        self.active_connections[session_id].append(websocket)
        
        # Send initial phase data if available
        phases = phase_tracker.get_formatted_phases(session_id)
        if phases:
            try:
                logger.info(f"Sending initial phases for session {session_id}: {len(phases)} phases")
                await websocket.send_json({"phases": phases})
            except Exception as e:
                logger.error(f"Error sending initial phases: {str(e)}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a websocket client"""
        try:
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)
                    logger.info(f"Removed connection for session {session_id}, remaining: {len(self.active_connections[session_id])}")
                    
                # Remove session if no connections left
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    logger.info(f"Removed session {session_id} from active connections")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")
    
    async def broadcast_phase_update(self, session_id: str, phase_data: Dict[str, Any]):
        """Broadcast phase updates to all connected clients for a session"""
        if session_id not in self.active_connections:
            logger.debug(f"No active connections for session {session_id}")
            return
            
        # Get properly formatted phases
        try:
            phases = phase_tracker.get_formatted_phases(session_id)
            if not phases:
                logger.debug(f"No phases to broadcast for session {session_id}")
                return
                
            status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
            for phase in phases:
                status = phase.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
                    
            logger.info(f"Broadcasting phases for session {session_id}: {status_counts}")
            
            # Send to all active connections for this session
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_json({"phases": phases})
                except WebSocketDisconnect:
                    disconnected.append(websocket)
                    logger.info(f"Connection disconnected during broadcast for session {session_id}")
                except Exception as e:
                    disconnected.append(websocket)
                    logger.error(f"Error sending phase update: {str(e)}")
                    
            # Clean up disconnected clients
            for ws in disconnected:
                self.disconnect(ws, session_id)
                
        except Exception as e:
            logger.error(f"Error in broadcast_phase_update: {str(e)}")
            traceback.print_exc()

# Create subscription manager
phase_subscription = PhaseSubscription()

# Register callback to broadcast phase updates
def phase_update_callback(session_id: str, phase_data: Dict[str, Any]):
    """Callback for phase updates from the phase tracker"""
    try:
        # Log the phase update
        current_phase = None
        phase_status = "unknown"
        
        # Find the current phase if any
        for tag in phase_data.get('tags', []):
            if tag in COMPILATION_PHASES:
                current_phase = tag
                break
                
        # Determine status
        if current_phase:
            if 'phase_start' in phase_data.get('tags', []):
                phase_status = "started"
            elif 'phase_end' in phase_data.get('tags', []):
                phase_status = "completed"
            else:
                phase_status = "updated"
                
        logger.info(f"Phase update for session {session_id}: {current_phase} - {phase_status}")
        
        # Run broadcast in background to avoid blocking
        asyncio.create_task(phase_subscription.broadcast_phase_update(session_id, phase_data))
    except Exception as e:
        logger.error(f"Error in phase_update_callback: {str(e)}")
        traceback.print_exc()

# Register callback with phase tracker
phase_tracker.register_callback(phase_update_callback)

def extract_agent_phases(agent, result):
    """Extract agent phases from the agent's compiler context, including multiple attempts"""
    session_id = None
    
    # Try to get the compiler and its last context
    compiler = agent.compiler if hasattr(agent, "compiler") else None
    context = compiler._last_context if compiler and hasattr(compiler, "_last_context") else None
    
    if context and hasattr(context, "compilation_session_id"):
        session_id = context.compilation_session_id
        # Get formatted phases from the phase tracker
        phases = phase_tracker.get_formatted_phases(session_id)
        
        # If we have phases from the tracker, use them
        if phases:
            # Include attempt information if available
            if hasattr(result, "attempts") and result.attempts > 1:
                # For multi-attempt cases, ensure attempt number is included
                # This will be recognized and displayed by the frontend
                for phase in phases:
                    if "attempt" not in phase:
                        # Check if we can extract attempt number from phase metadata
                        # This assumes "attempt_X" is in phase id or tags
                        if "attempt_" in phase.get("id", ""):
                            attempt_num = phase.get("id").split("attempt_")[1].split("_")[0]
                            phase["attempt"] = int(attempt_num)
                        else:
                            # Default to attempt 1 if not found
                            phase["attempt"] = 1
            
            return phases
    
    # Fallback to manual phase extraction if phase tracker doesn't have data
    phases = []
    attempts_data = {}
    current_attempt = 1
    
    # Try to extract attempts information
    if hasattr(result, "attempts"):
        current_attempt = result.attempts
    
    # Extract phase data for the current attempt
    if context and hasattr(context, "phase_results"):
        phase_results = context.phase_results
        
        # Check if we have multiple attempts data
        if hasattr(context, "attempts_data") and context.attempts_data:
            attempts_data = context.attempts_data
        
        # Schema Analysis phase
        if "schema_analysis" in phase_results:
            schema_analysis = phase_results["schema_analysis"]
            # Format the schema analysis data for better readability
            tables_info = []
            if "tables" in schema_analysis:
                for table in schema_analysis["tables"]:
                    tables_info.append(f"• {table}")
                    
            columns_info = []
            if "columns" in schema_analysis:
                for table, columns in schema_analysis["columns"].items():
                    columns_info.append(f"• {table}: {', '.join(columns)}")
            
            joins_info = []
            if "joins" in schema_analysis:
                for join in schema_analysis["joins"]:
                    joins_info.append(f"• {join['left']} ⟷ {join['right']}")
                    
            content = "**Tables Identified:**\n" + "\n".join(tables_info) + "\n\n"
            if columns_info:
                content += "**Columns Referenced:**\n" + "\n".join(columns_info) + "\n\n"
            if joins_info:
                content += "**Join Relationships:**\n" + "\n".join(joins_info)
                
            phases.append({
                "id": f"schema_analysis_attempt_{current_attempt}",
                "name": "Schema Analysis",
                "status": "completed",
                "thinking": content,
                "attempt": current_attempt
            })
        
        # Plan Generation phase
        if "plan_generation" in phase_results:
            plan_data = phase_results["plan_generation"]
            plan_text = plan_data.get("plan", "No plan available")
            
            # Include LLM thinking if available
            llm_thinking = ""
            if "llm_response" in plan_data:
                llm_thinking = plan_data.get("llm_response", "")
                # Prepend the LLM thinking before the plan
                if llm_thinking:
                    plan_text = f"**LLM Planning:**\n\n{llm_thinking}\n\n**Execution Plan:**\n\n{plan_text}"
            
            # Format the plan with bullet points for better readability
            formatted_plan = ""
            for line in plan_text.split("\n"):
                line = line.strip()
                if line:
                    # Add bullet points to steps
                    if line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                        formatted_plan += f"**{line}**\n"
                    else:
                        formatted_plan += f"{line}\n"
            
            phases.append({
                "id": f"query_planning_attempt_{current_attempt}",
                "name": "Query Planning",
                "status": "completed",
                "thinking": formatted_plan,
                "attempt": current_attempt
            })
        
        # Code Generation phase
        if "code_generation" in phase_results:
            code_data = phase_results["code_generation"]
            code = code_data.get("code", "")
            
            # Include LLM thinking if available
            llm_thinking = ""
            if "llm_response" in code_data:
                llm_thinking = code_data.get("llm_response", "")
                thinking = f"**LLM Reasoning:**\n\n{llm_thinking}\n\n**Generated PySpark code:**\n```python\n{code}\n```"
            else:
                thinking = "Generated PySpark code:\n```python\n" + code + "\n```"
            
            phases.append({
                "id": f"code_generation_attempt_{current_attempt}",
                "name": "Code Generation",
                "status": "completed",
                "thinking": thinking,
                "attempt": current_attempt
            })
        
        # Code Review phase
        if "code_review" in phase_results:
            review_data = phase_results["code_review"]
            passed = review_data.get("passed", False)
            
            # Include LLM thinking if available
            llm_thinking = ""
            if "llm_response" in review_data:
                llm_thinking = review_data.get("llm_response", "")
            
            if passed:
                review_content = "✅ Code passed review"
                if llm_thinking:
                    review_content = f"**LLM Review:**\n\n{llm_thinking}\n\n{review_content}"
                if "suggestions" in review_data:
                    review_content += f"\n\n{review_data['suggestions']}"
            else:
                review_content = "⚠️ Code review found issues"
                if llm_thinking:
                    review_content = f"**LLM Review:**\n\n{llm_thinking}\n\n{review_content}"
                if "issues" in review_data:
                    review_content += f"\n\n{review_data['issues']}"
            
            phases.append({
                "id": f"code_review_attempt_{current_attempt}",
                "name": "Code Review",
                "status": "completed",
                "thinking": review_content,
                "attempt": current_attempt
            })
    
    # Add execution phase based on result
    if result.success:
        execution_content = f"Query executed successfully in {result.execution_time:.3f} seconds."
        
        # Add row count if available
        if hasattr(result, "row_count") and result.row_count is not None:
            execution_content += f"\nReturned {result.row_count} rows."
        elif hasattr(result.result_data, "count"):
            try:
                row_count = result.result_data.count()
                execution_content += f"\nReturned {row_count} rows."
            except:
                pass
        
        phases.append({
            "id": f"executing_query_attempt_{current_attempt}",
            "name": "Executing Query",
            "status": "completed",
            "thinking": execution_content,
            "attempt": current_attempt
        })
    else:
        error_message = str(result.error) if result.error else "Unknown error occurred."
        
        # If there were multiple attempts, indicate that this was the final failing attempt
        if current_attempt > 1:
            error_message = f"Attempt {current_attempt} failed: {error_message}"
        
        phases.append({
            "id": f"executing_query_attempt_{current_attempt}",
            "name": "Executing Query",
            "status": "failed",
            "thinking": f"Error: {error_message}",
            "attempt": current_attempt
        })
    
    # Include information about previous attempts
    if attempts_data and len(attempts_data) > 0:
        # Sort attempts by attempt number
        for attempt_num, attempt_data in sorted(attempts_data.items()):
            if int(attempt_num) == current_attempt:
                continue  # Skip current attempt as we've already processed it
            
            # Include indicator about retry
            phases.append({
                "id": f"attempt_{attempt_num}_retry",
                "name": f"Attempt {attempt_num} Failed - Retrying",
                "status": "failed",
                "thinking": f"The agent's attempt {attempt_num} failed and is being retried.",
                "attempt": int(attempt_num),
                "is_retry_indicator": True
            })
            
            # Add phases from each previous attempt
            for phase_name, phase_data in attempt_data.items():
                if phase_name in ["schema_analysis", "plan_generation", "code_generation", "code_review"]:
                    display_name = PHASE_DISPLAY_NAMES.get(phase_name, phase_name.replace("_", " ").title())
                    thinking = phase_data.get("result", "No output available.")
                    
                    # Get LLM response if available
                    if "llm_response" in phase_data:
                        llm_thinking = phase_data.get("llm_response", "")
                        if llm_thinking and phase_name == "code_generation":
                            code = phase_data.get("code", "")
                            thinking = f"**LLM Reasoning:**\n\n{llm_thinking}\n\n**Generated Code:**\n```python\n{code}\n```"
                        elif llm_thinking:
                            thinking = f"**LLM Output:**\n\n{llm_thinking}\n\n{thinking}"
                    
                    phases.append({
                        "id": f"{phase_name}_attempt_{attempt_num}",
                        "name": display_name,
                        "status": "failed",
                        "thinking": thinking,
                        "attempt": int(attempt_num)
                    })
    
    # Sort phases by attempt number and predefined phase order
    phase_order = {
        "schema_analysis": 0,
        "query_planning": 1,
        "code_generation": 2,
        "code_review": 3,
        "executing_query": 4
    }
    
    def get_phase_order(phase):
        # Extract the phase name without attempt information
        phase_id = phase.get("id", "")
        for key in phase_order.keys():
            if key in phase_id:
                return phase.get("attempt", 1) * 100 + phase_order.get(key, 99)
        return 999  # Default high value for unknown phases
    
    sorted_phases = sorted(phases, key=get_phase_order)
    return sorted_phases

# Add a direct schema loading function to work around the schema_memory interface issue
def load_schema_directly(postgres_config):
    """
    Load database schema directly using psycopg2.
    This is a workaround for the schema memory interface mismatch.
    """
    try:
        logger.info("Loading database schema directly...")
        conn = psycopg2.connect(
            host=postgres_config["host"],
            port=postgres_config["port"],
            database=postgres_config["database"],
            user=postgres_config["user"],
            password=postgres_config["password"]
        )
        
        # Get tables
        tables = []
        columns = {}
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            for row in cursor:
                table_name = row[0]
                tables.append(table_name)
                
                # Get columns for each table
                column_cursor = conn.cursor()
                column_cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns[table_name] = []
                for col_row in column_cursor:
                    columns[table_name].append(col_row[0])
        
        conn.close()
        return {"tables": tables, "columns": columns}
    except Exception as e:
        logger.error(f"Error loading schema directly: {str(e)}")
        return {"tables": [], "columns": {}}

def format_results_from_df(df, limit=100):
    """Format results from DataFrame for API response"""
    if df is None:
        return []
    
    # For PySpark DataFrame
    if hasattr(df, "toPandas"):
        try:
            pdf = df.limit(limit).toPandas()
            return pdf.to_dict('records')
        except Exception as e:
            logger.error(f"Error converting to pandas: {str(e)}")
    
    # Try direct collection if toPandas failed
    if hasattr(df, "collect"):
        try:
            rows = df.limit(limit).collect()
            return [row.asDict() for row in rows]
        except Exception as e:
            logger.error(f"Error collecting rows: {str(e)}")
    
    # Last resort
    return []

# Load connections on startup
load_connections()

# API Routes
@app.get("/")
async def root():
    return {"message": "SparkSQL Agent API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    connection_count = len(DB_CONNECTIONS)
    agent_count = len(AGENT_INSTANCES)
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "connections": connection_count,
        "agents": agent_count,
    }

@app.get("/connections")
async def get_connections():
    """Get all database connections (with masked passwords)"""
    try:
        # Ensure DB_CONNECTIONS is loaded
        if not DB_CONNECTIONS and os.path.exists(CONNECTIONS_FILE):
            load_connections()
            
        sanitized = {}
        for conn_id, conn in DB_CONNECTIONS.items():
            try:
                conn_copy = conn.copy()
                if "password" in conn_copy:
                    conn_copy["password"] = "••••••••"
                sanitized[conn_id] = conn_copy
            except Exception as e:
                logger.error(f"Error processing connection {conn_id}: {str(e)}")
                
        logger.info(f"Returning {len(sanitized)} connections")
        return sanitized
    except Exception as e:
        logger.error(f"Error retrieving connections: {str(e)}")
        return {}

@app.post("/connections")
async def create_connection(connection: DatabaseConnection):
    """Create a new database connection"""
    try:
        # Generate a unique connection ID
        connection_id = str(uuid.uuid4())
        logger.info(f"Creating new connection '{connection.name}' with ID {connection_id}")
    
        # Store connection
        DB_CONNECTIONS[connection_id] = connection.dict()
        save_connections()
        
        # Log the created connection (without password)
        conn_dict = connection.dict()
        if "password" in conn_dict:
            conn_dict["password"] = "••••••••"
        logger.info(f"Created connection: {json.dumps(conn_dict)}")
    
        return {"id": connection_id, "status": "connected"}
    except Exception as e:
        logger.error(f"Error creating connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create connection: {str(e)}")

@app.put("/connections/{connection_id}")
async def update_connection(connection_id: str, connection: DatabaseConnection):
    """Update an existing database connection"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Update connection
    DB_CONNECTIONS[connection_id] = connection.dict()
    save_connections()
    
    # If we have a cached agent, remove it so it will be recreated with new connection details
    if connection_id in AGENT_INSTANCES:
        AGENT_INSTANCES[connection_id].shutdown()
        del AGENT_INSTANCES[connection_id]
    
    return {"id": connection_id, "status": "updated"}

@app.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a database connection"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Delete connection
    del DB_CONNECTIONS[connection_id]
    save_connections()
    
    # If we have a cached agent, remove it
    if connection_id in AGENT_INSTANCES:
        AGENT_INSTANCES[connection_id].shutdown()
        del AGENT_INSTANCES[connection_id]
    
    return {"status": "deleted"}

@app.get("/schema/{connection_id}")
async def get_schema(connection_id: str):
    """Get database schema for a connection using the agent's schema memory"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    try:
        # Get or create agent
        agent = get_or_create_agent(connection_id)
        
        # Get schema from agent's schema memory
        if hasattr(agent, 'schema_memory') and agent.schema_memory:
            tables = agent.schema_memory.get_all_table_names()
            columns = {}
            
            # Get columns for each table
            for table in tables:
                columns[table] = agent.schema_memory.get_column_names(table)
            
            return {
                "tables": tables,
                "columns": columns
            }
        else:
                return {
                "tables": [],
                "columns": {}
                }
    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

@app.post("/query")
async def process_query(query_request: Query):
    """Process a natural language query with the SparkSQL agent"""
    start_time = time.time()
    
    try:
        # Get or create agent instance for this connection
        connection_id = query_request.connection_id
        if connection_id not in DB_CONNECTIONS:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        query_text = query_request.query
        connection = DB_CONNECTIONS[connection_id]
        
        logger.info(f"Processing query: '{query_text}' for connection {connection_id}")
        
        agent = get_or_create_agent(connection_id)
        
        # Process query and get result
        try:
            # Generate and execute the query
            result = agent.process_request(query_text)
            
            # Extract agent thinking phases
            phases = extract_agent_phases(agent, result)
            
            # Calculate API execution time
            api_execution_time = time.time() - start_time
            
            # Get actual query execution time from the agent result 
            query_execution_time = result.execution_time if hasattr(result, 'execution_time') else None
            
            # Extract attempts information
            attempts_count = result.attempts if hasattr(result, 'attempts') else 1
            
            if result.success:
                logger.info(f"Query executed successfully in {api_execution_time:.2f} seconds (query execution: {query_execution_time:.2f}s)")
                
                # Format results
                formatted_results = format_results_from_df(result.result_data)
                schema = []
                
                # Get schema if available
                if hasattr(result.result_data, "schema"):
                    try:
                        fields = result.result_data.schema.fields
                        schema = [{"name": field.name, "type": str(field.dataType)} for field in fields]
                    except Exception as e:
                        logger.error(f"Error getting schema: {str(e)}")
            
                return {
                    "success": True,
                    "executionTime": query_execution_time,  # Actual query execution time
                    "apiExecutionTime": api_execution_time,  # Total API execution time
                    "results": formatted_results,
                    "schema": schema,
                    "rowCount": len(formatted_results),
                    "attempts": attempts_count,
                    "agentPhases": [
                        {
                            "id": phase.get("id"),
                            "name": phase.get("name"),
                            "status": phase.get("status"),
                            "thinking": phase.get("thinking", ""),
                            "attempt": phase.get("attempt", 1),
                            "is_retry_indicator": phase.get("is_retry_indicator", False)
                        } for phase in phases
                    ],
                    "compilationSessionId": getattr(agent.compiler._last_context, "compilation_session_id", None)
                }
            else:
                logger.error(f"Query execution failed: {result.error}")
                return {
                    "success": False,
                    "executionTime": query_execution_time,  # Actual query execution time (may be None)
                    "apiExecutionTime": api_execution_time,  # Total API execution time
                    "error": str(result.error),
                    "attempts": attempts_count,
                    "agentPhases": [
                        {
                            "id": phase.get("id"),
                            "name": phase.get("name"),
                            "status": phase.get("status"),
                            "thinking": phase.get("thinking", ""),
                            "attempt": phase.get("attempt", 1),
                            "is_retry_indicator": phase.get("is_retry_indicator", False)
                        } for phase in phases
                    ],
                    "compilationSessionId": getattr(agent.compiler._last_context, "compilation_session_id", None)
                }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            execution_time = time.time() - start_time
            
            # Create error phases for UI display
            error_phases = [
                {
                    "id": "error",
                    "name": "Error",
                    "status": "failed",
                    "thinking": f"Agent processing error: {str(e)}\n\n{traceback.format_exc()}",
                    "attempt": 1
                }
            ]
            
            return {
                "success": False,
                "executionTime": None,  # No execution time for errors
                "apiExecutionTime": execution_time,  # Total API execution time
                "error": str(e),
                "attempts": 1,  # Failed on first attempt
                "agentPhases": [
                    {
                        "id": phase.get("id"),
                        "name": phase.get("name"),
                        "status": phase.get("status"),
                        "thinking": phase.get("thinking", ""),
                        "attempt": phase.get("attempt", 1),
                        "is_retry_indicator": phase.get("is_retry_indicator", False)
                    } for phase in error_phases
                ]
            }
    except Exception as e:
        logger.error(f"Error in query processing endpoint: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/phases/{session_id}")
async def websocket_phases(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time phase updates"""
    logger.info(f"New WebSocket connection for session {session_id}")
    try:
        await phase_subscription.connect(websocket, session_id)
        
        # Keep the connection open
        while True:
            try:
                # Wait for client messages (e.g., ping)
                message = await websocket.receive_text()
                
                # Simple ping-pong protocol
                if message == "ping":
                    # Send fresh phase data when we get a ping
                    phases = phase_tracker.get_formatted_phases(session_id)
                    await websocket.send_json({"phases": phases})
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                phase_subscription.disconnect(websocket, session_id)
                break
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {str(e)}")
                # Don't break the connection on a single message error
                continue
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during setup for session {session_id}")
        phase_subscription.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            # Attempt to send an error message to the client
            await websocket.send_json({"error": str(e)})
        except:
            # If that fails, just disconnect cleanly
            pass
        phase_subscription.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get('/test-docker-host')
async def test_docker_host():
    '''Test connections to localhost and host.docker.internal'''
    results = {
        'localhost': {'success': False, 'error': None},
        'host.docker.internal': {'success': False, 'error': None}
    }
    
    # Test localhost connection
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='postgres'
        )
        conn.close()
        results['localhost']['success'] = True
    except Exception as e:
        results['localhost']['error'] = str(e)
    
    # Test host.docker.internal connection
    try:
        conn = psycopg2.connect(
            host='host.docker.internal',
            port=5432,
            database='postgres',
            user='postgres',
            password='postgres'
        )
        conn.close()
        results['host.docker.internal']['success'] = True
    except Exception as e:
        results['host.docker.internal']['error'] = str(e)
    
    return results

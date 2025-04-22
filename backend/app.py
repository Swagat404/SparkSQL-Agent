from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import json
import time
import subprocess
import tempfile
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_DIR = os.path.join(ROOT_DIR, "spark_pg_agent_formal")
CONNECTIONS_FILE = os.path.join(ROOT_DIR, "connections.json")

# Add ROOT_DIR to path for imports
sys.path.insert(0, ROOT_DIR)

# Try to import agent modules, with fallback for testing environments
try:
    from spark_pg_agent_formal.cli.cli import run_agent_command
    from spark_pg_agent_formal.core.transformation_agent import TransformationAgent
    from spark_pg_agent_formal.db.database_manager import DatabaseManager
    from spark_pg_agent_formal.db.schema_memory import SchemaMemory
    AGENT_AVAILABLE = True
except ImportError:
    logger.warning("Could not import SparkSQL Agent modules. Running in mock mode.")
    AGENT_AVAILABLE = False

app = FastAPI(title="SparkSQL Agent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connections store - persisted across requests
# In production, this should be stored in a database
DB_CONNECTIONS = {}

# Load connections from file if it exists
def load_connections():
    global DB_CONNECTIONS
    try:
        if os.path.exists(CONNECTIONS_FILE):
            with open(CONNECTIONS_FILE, 'r') as f:
                connections = json.load(f)
                DB_CONNECTIONS = connections
                logger.info(f"Loaded {len(connections)} connections from {CONNECTIONS_FILE}")
        else:
            logger.info(f"No connections file found at {CONNECTIONS_FILE}")
    except Exception as e:
        logger.error(f"Error loading connections: {str(e)}")

# Save connections to file
def save_connections():
    try:
        with open(CONNECTIONS_FILE, 'w') as f:
            json.dump(DB_CONNECTIONS, f, indent=2)
            logger.info(f"Saved {len(DB_CONNECTIONS)} connections to {CONNECTIONS_FILE}")
    except Exception as e:
        logger.error(f"Error saving connections: {str(e)}")

# Load connections on startup
load_connections()

# Store active agent sessions
AGENT_SESSIONS = {}

# Pydantic models
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

class AgentPhase(BaseModel):
    phase: str
    content: str
    status: str = "completed"

# Routes
@app.get("/")
async def root():
    return {"message": "SparkSQL Agent API is running", "agent_available": AGENT_AVAILABLE}

@app.get("/connections")
async def list_connections():
    """List all connections"""
    logger.info(f"Listing {len(DB_CONNECTIONS)} connections")
    return DB_CONNECTIONS

@app.post("/connections")
async def create_connection(connection: DatabaseConnection):
    """Create a new database connection"""
    connection_id = str(uuid.uuid4())
    
    # Test connection before storing
    if AGENT_AVAILABLE:
        try:
            test_connection(connection)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
    
    # Store connection without password in memory (in production, encrypt the password)
    conn_dict = connection.dict()
    if "password" in conn_dict:
        # In production: encrypt the password
        pass
    
    DB_CONNECTIONS[connection_id] = conn_dict
    save_connections()  # Save to file
    
    return {"id": connection_id, "status": "connected"}

@app.post("/test-connection")
async def test_connection_endpoint(connection: DatabaseConnection):
    """Test a database connection without creating it"""
    logger.info(f"Testing connection to {connection.type} database: {connection.host}:{connection.port}/{connection.database}")
    
    try:
        # Test the connection
        if AGENT_AVAILABLE:
            test_connection(connection)
        else:
            # In mock mode, simulate a successful connection test
            # In reality, we'd actually test the connection
            time.sleep(1)  # Simulate a delay
            
            # Fail for invalid credentials (for demonstration)
            if connection.username == "invalid" or connection.password == "invalid":
                raise ValueError("Invalid credentials")
        
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.put("/connections/{connection_id}")
async def update_connection(connection_id: str, connection: DatabaseConnection):
    """Update an existing connection"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Test connection before updating
    if AGENT_AVAILABLE:
        try:
            test_connection(connection)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
    
    # Update connection
    conn_dict = connection.dict()
    DB_CONNECTIONS[connection_id] = conn_dict
    save_connections()  # Save to file
    
    return {"id": connection_id, "status": "updated"}

@app.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a connection"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    del DB_CONNECTIONS[connection_id]
    save_connections()  # Save to file
    
    return {"status": "deleted"}

@app.get("/schema/{connection_id}")
async def get_schema(connection_id: str):
    """Get database schema for a connection"""
    if connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection = DB_CONNECTIONS[connection_id]
    
    if AGENT_AVAILABLE:
        try:
            # Initialize database manager for the connection
            db_manager = create_db_manager(connection)
            schema_memory = SchemaMemory()
            db_manager.load_schema(schema_memory)
            
            # Get tables and columns from schema memory
            tables = schema_memory.get_tables()
            columns = {}
            for table in tables:
                columns[table] = [col['name'] for col in schema_memory.get_columns(table)]
            
            return {
                "tables": tables,
                "columns": columns
            }
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")
    else:
        # Return mock schema for testing
        return {
            "tables": ["customers", "orders", "products", "order_items"],
            "columns": {
                "customers": ["customer_id", "name", "email", "country"],
                "orders": ["order_id", "customer_id", "order_date", "total_amount", "status"],
                "products": ["product_id", "name", "category", "price", "stock"],
                "order_items": ["item_id", "order_id", "product_id", "quantity", "price_per_unit"]
            }
        }

@app.post("/query")
async def execute_query(query_request: Query):
    """Execute a query using the SparkSQL Agent"""
    if query_request.connection_id not in DB_CONNECTIONS:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection = DB_CONNECTIONS[query_request.connection_id]
    query_text = query_request.query.strip()
    
    # Log query request
    logger.info(f"Processing query: '{query_text}' on connection: {connection['name']}")
    
    try:
        # Execute query using the agent
        if AGENT_AVAILABLE:
            # Use real agent
            result, phases = run_real_agent(query_text, connection)
        else:
            # Use mock agent (for testing/development)
            result, phases = run_mock_agent(query_text, connection)
        
        # Format the result and phases for return
        return {
            "result": result.get("rows", []),
            "generated_code": get_agent_generated_code(phases),
            "execution_time": result.get("execution_time", 0),
            "timestamp": datetime.now().isoformat(),
            "agent_phases": phases,
            "ai_thinking": f"### AI Agent Thinking Process\n{get_agent_thinking_output(phases)}",
            "ai_response": result.get("ai_response", "Query processed successfully."),
            "connection_info": {
                "name": connection.get("name", "Unknown"),
                "type": connection.get("type", "Unknown"),
                "database": connection.get("database", "Unknown")
            }
        }
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

def test_connection(connection: DatabaseConnection):
    """Test database connection"""
    db_manager = create_db_manager(connection.dict())
    db_manager.test_connection()
    return True

def create_db_manager(connection_details):
    """Create a database manager from connection details"""
    db_type = connection_details.get("type", "")
    
    if db_type.lower() in ["postgresql", "postgres"]:
        return DatabaseManager(
            host=connection_details.get("host", ""),
            port=connection_details.get("port", 0),
            dbname=connection_details.get("database", ""),
            user=connection_details.get("username", ""),
            password=connection_details.get("password", ""),
            db_type="postgresql"
        )
    elif db_type.lower() in ["mysql"]:
        return DatabaseManager(
            host=connection_details.get("host", ""),
            port=connection_details.get("port", 0),
            dbname=connection_details.get("database", ""),
            user=connection_details.get("username", ""),
            password=connection_details.get("password", ""),
            db_type="mysql"
        )
    elif db_type.lower() in ["spark", "sparksql"]:
        # Handle Spark connection (if supported by your DatabaseManager)
        return DatabaseManager(
            host=connection_details.get("host", ""),
            port=connection_details.get("port", 0),
            dbname=connection_details.get("database", ""),
            user=connection_details.get("username", ""),
            password=connection_details.get("password", ""),
            db_type="spark"
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def run_real_agent(query_text, connection_details):
    """Run the actual agent with the query and connection details"""
    # Create database manager for the connection
    db_manager = create_db_manager(connection_details)
    
    # Create schema memory
    schema_memory = SchemaMemory()
    db_manager.load_schema(schema_memory)
    
    # Create a temporary directory for agent output
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "agent_log.txt")
        
        # Prepare agent environment
        agent = TransformationAgent(db_manager, schema_memory, log_file=log_file)
        
        # Start timing
        start_time = datetime.now()
        
        # Process the request
        result, code = agent.process_request(query_text)
        
        # End timing
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Extract phases from the agent log
        phases = parse_agent_log(log_file)
        
        # Format the result
        if hasattr(result, "to_dict"):
            result_dict = result.to_dict(orient="records")
        else:
            result_dict = result if isinstance(result, list) else [result]
        
        # Generate a response message based on the result
        ai_response = generate_response_message(query_text, result_dict)
        
        return {
            "rows": result_dict,
            "execution_time": execution_time,
            "ai_response": ai_response
        }, phases

def parse_agent_log(log_file):
    """Parse the agent log file to extract phases"""
    phases = []
    current_phase = None
    current_content = []
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
            for line in lines:
                # Check for phase headers
                if "PHASE:" in line and "=" * 10 in line:
                    # Save the previous phase if it exists
                    if current_phase and current_content:
                        phases.append({
                            "phase": current_phase,
                            "content": "".join(current_content).strip(),
                            "status": "completed"
                        })
                    
                    # Start a new phase
                    phase_match = re.search(r"PHASE: ([A-Z_]+)", line)
                    if phase_match:
                        current_phase = phase_match.group(1)
                        current_content = []
                
                # Check for response markers
                elif "RESPONSE:" in line and current_phase:
                    # Continue collecting content
                    continue
                
                # Collect content lines
                elif current_phase and not line.startswith("==="):
                    current_content.append(line)
        
        # Add the last phase if it exists
        if current_phase and current_content:
            phases.append({
                "phase": current_phase,
                "content": "".join(current_content).strip(),
                "status": "completed"
            })
    
    except Exception as e:
        logger.error(f"Error parsing agent log: {str(e)}")
        # Return an empty phase list on error
        return []
    
    return phases

def generate_response_message(query, results):
    """Generate a natural language response based on the query and results"""
    if not results:
        return "I couldn't find any results matching your query."
    
    # Determine the type of query
    query_lower = query.lower()
    
    if "product" in query_lower or "sell" in query_lower:
        return f"Here are the product details you requested. The results show information about {len(results)} products."
    
    if "customer" in query_lower:
        return f"I found {len(results)} customers matching your query. The results show basic information including ID, name, email, and country."
    
    if "order" in query_lower:
        return f"Here are the orders you requested. The results include details for {len(results)} orders."
    
    # Default response
    return f"I found {len(results)} records matching your query."

def run_mock_agent(query_text, connection_details):
    """
    Mock agent execution for testing/development environments
    where the actual agent code is not available
    """
    # Create a unique ID for this query based on text and connection
    query_hash = hash(f"{query_text}_{connection_details.get('name', '')}")
    
    # Generate different phases based on the query text
    phases = generate_mock_phases(query_text)
    
    # Generate mock results based on the query
    results = generate_mock_results(query_text, connection_details)
    
    # Add a delay to simulate processing time
    time.sleep(1.0)
    
    return results, phases

def generate_mock_phases(query_text):
    """Generate mock agent phases based on the query text"""
    query_lower = query_text.lower()
    phases = []
    
    # Schema Analysis phase
    schema_content = {"tables": [], "columns": {}, "joins": [], "explanation": ""}
    
    if "product" in query_lower or "selling" in query_lower:
        schema_content["tables"] = ["products", "order_items", "orders"]
        schema_content["columns"] = {
            "products": ["product_id", "name", "category", "price", "stock"],
            "order_items": ["item_id", "order_id", "product_id", "quantity", "price_per_unit"],
            "orders": ["order_id", "order_date"]
        }
        schema_content["joins"] = [
            {"left_table": "products", "left_column": "product_id", "right_table": "order_items", "right_column": "product_id"},
            {"left_table": "order_items", "left_column": "order_id", "right_table": "orders", "right_column": "order_id"}
        ]
        schema_content["explanation"] = f"To determine the top selling products, we need to analyze sales data from order_items, linking to products for details and orders for dates."
    
    elif "customer" in query_lower:
        schema_content["tables"] = ["customers", "orders"]
        schema_content["columns"] = {
            "customers": ["customer_id", "name", "email", "country"],
            "orders": ["order_id", "customer_id", "order_date", "total_amount"]
        }
        schema_content["joins"] = [
            {"left_table": "customers", "left_column": "customer_id", "right_table": "orders", "right_column": "customer_id"}
        ]
        schema_content["explanation"] = f"For information about customers, we need to access the customers table and potentially join with orders for purchase history."
    
    elif "order" in query_lower:
        schema_content["tables"] = ["orders", "customers"]
        schema_content["columns"] = {
            "orders": ["order_id", "customer_id", "order_date", "total_amount"],
            "customers": ["customer_id", "name", "email"]
        }
        schema_content["joins"] = [
            {"left_table": "orders", "left_column": "customer_id", "right_table": "customers", "right_column": "customer_id"}
        ]
        schema_content["explanation"] = f"To retrieve order information, we need the orders table with customer details from the customers table."
    
    # Add Schema Analysis phase
    phases.append({
        "phase": "SCHEMA_ANALYSIS",
        "content": json.dumps(schema_content, indent=4),
        "status": "completed"
    })
    
    # Add Plan Generation phase
    plan_content = f"""Execution Plan for: "{query_text}"

1. **Identify Required Tables and Columns:**
   - Based on the schema analysis, we need {", ".join(schema_content["tables"])}
   - Select relevant columns for the query

2. **Define Join Strategy:**
   - Join tables using appropriate keys
   - Ensure proper join types (inner, left, etc.)

3. **Apply Filtering and Aggregation:**
   - Filter data based on query requirements
   - Apply aggregations if needed for statistics
   - Sort results appropriately

4. **Optimize Execution:**
   - Use appropriate indexing
   - Consider partitioning for large datasets
   - Apply push-down predicates when possible
"""
    phases.append({
        "phase": "PLAN_GENERATION",
        "content": plan_content,
        "status": "completed"
    })
    
    # Generate code based on the query
    if "product" in query_lower or "selling" in query_lower:
        code = """```python
# Necessary imports
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Create a SparkSession
spark = SparkSession.builder\\
    .appName("Top Selling Products Analysis")\\
    .getOrCreate()

# Connect to the database
jdbc_url = f"jdbc:{connection_type}://{host}:{port}/{database}"
connection_properties = {
    "user": username,
    "password": password,
    "driver": driver_class
}

# Load the necessary tables
products_df = spark.read.jdbc(url=jdbc_url, table="products", properties=connection_properties)
order_items_df = spark.read.jdbc(url=jdbc_url, table="order_items", properties=connection_properties)

# Calculate total sales per product
sales_per_product = order_items_df.groupBy("product_id")\\
    .agg(
        F.sum("quantity").alias("total_quantity_sold"),
        F.sum(F.col("quantity") * F.col("price_per_unit")).alias("total_revenue")
    )

# Join with products to get product details
top_products = sales_per_product.join(
    products_df,
    sales_per_product["product_id"] == products_df["product_id"],
    "inner"
)\\
.select(
    products_df["product_id"],
    products_df["name"],
    products_df["category"],
    products_df["price"],
    sales_per_product["total_quantity_sold"],
    sales_per_product["total_revenue"]
)\\
.orderBy(F.col("total_revenue").desc())

# Get the top N results
result_df = top_products.limit(10)

# Show the results
result_df.show()
```"""
    elif "customer" in query_lower:
        code = """```python
# Necessary imports
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Create a SparkSession
spark = SparkSession.builder\\
    .appName("Customer Query")\\
    .getOrCreate()

# Connect to the database
jdbc_url = f"jdbc:{connection_type}://{host}:{port}/{database}"
connection_properties = {
    "user": username,
    "password": password,
    "driver": driver_class
}

# Load the customers table
customers_df = spark.read.jdbc(url=jdbc_url, table="customers", properties=connection_properties)

# Select relevant columns
result_df = customers_df.select(
    "customer_id",
    "name",
    "email",
    "country"
)

# Show the results
result_df.show()
```"""
    else:
        code = """```python
# Necessary imports
from pyspark.sql import SparkSession

# Create a SparkSession
spark = SparkSession.builder\\
    .appName("Order Query")\\
    .getOrCreate()

# Connect to the database
jdbc_url = f"jdbc:{connection_type}://{host}:{port}/{database}"
connection_properties = {
    "user": username,
    "password": password,
    "driver": driver_class
}

# Load the orders table
orders_df = spark.read.jdbc(url=jdbc_url, table="orders", properties=connection_properties)

# Select relevant columns
result_df = orders_df.select(
    "order_id",
    "customer_id",
    "order_date",
    "total_amount"
)

# Show the results
result_df.show()
```"""
    
    # Add Code Generation phase
    phases.append({
        "phase": "CODE_GENERATION",
        "content": code,
        "status": "completed"
    })
    
    # Add Code Review phase
    phases.append({
        "phase": "CODE_REVIEW",
        "content": """The generated code has been reviewed for:

1. **Functionality** - Verifying it will produce the correct results
2. **Performance** - Ensuring efficient execution
3. **Error Handling** - Added safeguards against potential issues
4. **Security** - Checking for potential vulnerabilities

The code looks good and should execute successfully.""",
        "status": "completed"
    })
    
    # Add Final Code phase
    phases.append({
        "phase": "FINAL_CODE",
        "content": code,
        "status": "completed"
    })
    
    return phases

def generate_mock_results(query_text, connection_details):
    """Generate mock results based on the query text"""
    query_lower = query_text.lower()
    execution_time = round(random.uniform(0.3, 1.5), 3)
    
    if "product" in query_lower or "selling" in query_lower:
        rows = [
            {"product_id": 101, "name": "Laptop", "category": "Electronics", "price": 1299.99, "total_quantity_sold": 256, "total_revenue": 332797.44},
            {"product_id": 102, "name": "Smartphone", "category": "Electronics", "price": 899.99, "total_quantity_sold": 418, "total_revenue": 376195.82},
            {"product_id": 103, "name": "Headphones", "category": "Electronics", "price": 149.99, "total_quantity_sold": 623, "total_revenue": 93443.77}
        ]
        response = f"I've identified the top selling products based on total revenue. The top product is {rows[0]['name']} with ${rows[0]['total_revenue']:.2f} in total sales. Would you like to see this data visualized in a chart?"
    
    elif "customer" in query_lower:
        rows = [
            {"customer_id": 1, "name": "John Doe", "email": "john@example.com", "country": "US"},
            {"customer_id": 2, "name": "Jane Smith", "email": "jane@example.com", "country": "UK"},
            {"customer_id": 3, "name": "Bob Johnson", "email": "bob@example.com", "country": "CA"}
        ]
        response = "Here are the customer details you requested. The results show basic information including ID, name, email, and country."
    
    else:
        rows = [
            {"order_id": 1001, "customer_id": 1, "order_date": "2023-04-01", "total_amount": 125.50},
            {"order_id": 1002, "customer_id": 2, "order_date": "2023-04-05", "total_amount": 89.99},
            {"order_id": 1003, "customer_id": 1, "order_date": "2023-04-10", "total_amount": 299.95}
        ]
        response = "Here are the orders you requested. The results show the order ID, customer ID, date, and total amount."
    
    return {
        "rows": rows,
        "execution_time": execution_time,
        "ai_response": response
    }

def get_agent_generated_code(phases):
    """Extract the final generated code from agent phases"""
    # Look for the FINAL_CODE phase
    for phase in phases:
        if phase["phase"] == "FINAL_CODE":
            # Extract code from markdown code blocks
            content = phase["content"]
            code_match = re.search(r'```(?:python)?\s*(.*?)\s*```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
    
    # If no final code found, return empty string
    return ""

def get_agent_thinking_output(phases):
    """
    Generate a consolidated thinking output from all phases
    for display in the chat UI
    """
    thinking_parts = []
    
    # Add schema analysis
    schema_phase = next((p for p in phases if p["phase"] == "SCHEMA_ANALYSIS"), None)
    if schema_phase:
        thinking_parts.append("1. Schema Analysis:")
        try:
            # Try to parse as JSON
            schema_data = json.loads(schema_phase["content"])
            tables = schema_data.get("tables", [])
            thinking_parts.append(f"   - Found relevant tables: {', '.join(tables)}")
            
            # Add join information
            joins = schema_data.get("joins", [])
            if joins:
                join_strs = []
                for join in joins:
                    join_strs.append(f"{join.get('left_table')}.{join.get('left_column')} = {join.get('right_table')}.{join.get('right_column')}")
                thinking_parts.append(f"   - Identified necessary joins: {'; '.join(join_strs)}")
        except:
            # Fallback if not JSON
            thinking_parts.append("   - Analyzed database schema")
            thinking_parts.append("   - Identified relevant tables and columns")
    
    # Add plan generation
    plan_phase = next((p for p in phases if p["phase"] == "PLAN_GENERATION"), None)
    if plan_phase:
        thinking_parts.append("\n2. Query Planning:")
        # Extract bullet points from the plan
        bullets = re.findall(r'\d+\.\s+\*\*.*?\*\*:.*?(?=\d+\.\s+\*\*|\Z)', plan_phase["content"], re.DOTALL)
        for bullet in bullets[:3]:  # Limit to first 3 bullet points
            clean_bullet = re.sub(r'\*\*|\n\s*', ' ', bullet).strip()
            thinking_parts.append(f"   - {clean_bullet}")
    
    # Add code generation
    code_phase = next((p for p in phases if p["phase"] == "CODE_GENERATION"), None)
    if code_phase:
        thinking_parts.append("\n3. Code Generation:")
        thinking_parts.append("   - Generated PySpark code")
        thinking_parts.append("   - Implemented table loading and column selection")
        thinking_parts.append("   - Set up proper joins and transformations")
    
    # Add code review
    review_phase = next((p for p in phases if p["phase"] == "CODE_REVIEW"), None)
    if review_phase:
        thinking_parts.append("\n4. Code Review and Optimization:")
        thinking_parts.append("   - Verified code correctness")
        thinking_parts.append("   - Applied best practices")
        thinking_parts.append("   - Ensured efficient execution")
    
    return "\n".join(thinking_parts)

if __name__ == "__main__":
    import uvicorn
    import random
    uvicorn.run(app, host="0.0.0.0", port=8000) 
#!/usr/bin/env python3
"""
Quickstart example for the Spark-Postgres Agent
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent from the correct location
from spark_pg_agent_formal import TransformationAgent
from spark_pg_agent_formal.core.types import AgentConfig

def main():
    # Configure PostgreSQL connection
    postgres_config = {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": os.getenv("PG_PORT", "5432"),
        "database": os.getenv("PG_DATABASE", "postgres"),
        "user": os.getenv("PG_USER", "postgres"),
        "password": os.getenv("PG_PASSWORD", "postgres")
    }
    
    # Create agent configuration
    config = AgentConfig(
        llm_provider="openai",
        enable_visualization=True,
        show_execution_plan=True
    )
    
    # Initialize the agent
    agent = TransformationAgent(postgres_config, config)
    
    # Run a query with the agent
    result = agent.run_query(
        "Load the customers table from Postgres, find the top 5 customers by total purchase amount, and create a bar chart visualization"
    )
    
    # Display the results
    print(result.text)
    
    # If there's a dataframe result, show it
    if hasattr(result, "dataframe") and result.dataframe is not None:
        print("\nDataFrame Result:")
        print(result.dataframe.head())
    
    # If there's a visualization, save it
    if hasattr(result, "visualization") and result.visualization is not None:
        result.visualization.savefig("top_customers.png")
        print("\nVisualization saved to top_customers.png")

if __name__ == "__main__":
    main() 
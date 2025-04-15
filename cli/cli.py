"""
Command-line interface for Spark PostgreSQL Agent.

This module provides the CLI for interacting with the agent.
"""

import os
import sys
import click
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pathlib import Path
import socket

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown

from spark_pg_agent_formal.core.agent import TransformationAgent
from spark_pg_agent_formal.core.types import AgentConfig
from spark_pg_agent_formal.db.db_manager import DatabaseDiscovery


# Load environment variables from .env file
load_dotenv()

# Create console for rich output
console = Console()


@click.group()
def cli():
    """Spark PostgreSQL Agent CLI."""
    pass


@cli.command()
@click.argument('request', required=False)
@click.option("--pg-host", default=None, help="PostgreSQL host")
@click.option("--pg-port", default=None, type=int, help="PostgreSQL port")
@click.option("--pg-db", default=None, help="PostgreSQL database name")
@click.option("--pg-user", default=None, help="PostgreSQL username")
@click.option("--pg-pass", default=None, help="PostgreSQL password")
@click.option("--llm-provider", default=lambda: os.environ.get("LLM_PROVIDER", "openai"), help="LLM provider (openai/anthropic)")
@click.option("--max-attempts", default=5, type=int, help="Maximum number of retry attempts")
@click.option("--optimization-level", default=1, type=int, help="Code optimization level (0-3)")
@click.option("--validation/--no-validation", default=True, help="Enable/disable result validation")
@click.option("--visualization/--no-visualization", default=False, help="Enable/disable result visualization")
def execute(request, pg_host, pg_port, pg_db, pg_user, pg_pass, llm_provider, max_attempts, 
           optimization_level, validation, visualization):
    """Execute a natural language transformation request."""
    # Initialize console for rich output
    console.print(Panel.fit("SparkPG Agent Execution", style="bold"))
    
    # Configure agent
    postgres_config = get_postgres_config(pg_host, pg_port, pg_db, pg_user, pg_pass)
    if not postgres_config:
        console.print("[red]Error: PostgreSQL connection details are required.[/red]")
        return
    
    # Initialize agent
    agent_config = AgentConfig(
        llm_provider=llm_provider,
        max_attempts=max_attempts,
        optimization_level=optimization_level,
        show_execution_plan=True,
        enable_visualization=visualization,
        validation_enabled=validation
    )
    
    try:
        agent = TransformationAgent(
            postgres_config=postgres_config,
            config=agent_config
        )
        
        # If no request is provided, switch to interactive mode
        if not request:
            interactive(pg_host, pg_port, pg_db, pg_user, pg_pass, llm_provider, max_attempts,
                      optimization_level, validation, visualization)
            return
        
        # Process the transformation request
        success, result = agent.process_request(request)
        
        if success:
            console.print("[green]Transformation successful![/green]")
            display_result(result)
        else:
            console.print("[red]Transformation failed.[/red]")
            if result and "error" in result:
                console.print(f"Error: {result['error']}")
        
    except Exception as e:
        console.print(f"[red]Error executing transformation: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
    finally:
        # Stop Spark session
        if 'agent' in locals():
            agent.shutdown()
            console.print("Execution completed.")


@cli.command()
@click.option("--pg-host", default=None, help="PostgreSQL host")
@click.option("--pg-port", default=None, type=int, help="PostgreSQL port")
@click.option("--pg-db", default=None, help="PostgreSQL database name")
@click.option("--pg-user", default=None, help="PostgreSQL username")
@click.option("--pg-pass", default=None, help="PostgreSQL password")
@click.option("--llm-provider", default=lambda: os.environ.get("LLM_PROVIDER", "openai"), help="LLM provider (openai/anthropic)")
@click.option("--max-attempts", default=5, type=int, help="Maximum number of retry attempts")
@click.option("--optimization-level", default=1, type=int, help="Code optimization level (0-3)")
@click.option("--validation/--no-validation", default=True, help="Enable/disable result validation")
@click.option("--visualization/--no-visualization", default=False, help="Enable/disable result visualization")
def interactive(pg_host, pg_port, pg_db, pg_user, pg_pass, llm_provider, max_attempts, 
               optimization_level, validation, visualization):
    """Run the agent in interactive mode."""
    # Disable tracing output in CLI mode
    os.environ["SPARK_PG_AGENT_QUIET_TRACING"] = "1"
    os.environ["SPARK_PG_AGENT_NO_SPINNER"] = "1"
    os.environ["AGENTTRACE_NO_SPINNER"] = "1"
    
    # Load the tracing module and disable console output
    from spark_pg_agent_formal.tracing import disable_console_output
    disable_console_output()
    
    console.print(Panel.fit("SparkPG Agent Interactive Mode", style="blue"))
    
    # Get PostgreSQL configuration
    postgres_config = get_postgres_config(pg_host, pg_port, pg_db, pg_user, pg_pass)
    if not postgres_config:
        console.print("[red]Error: PostgreSQL connection details are required.[/red]")
        return
    
    # Initialize agent
    agent_config = AgentConfig(
        llm_provider=llm_provider,
        max_attempts=max_attempts,
        optimization_level=optimization_level,
        show_execution_plan=True,
        enable_visualization=visualization,
        validation_enabled=validation
    )
    
    try:
        agent = TransformationAgent(
            postgres_config=postgres_config,
            config=agent_config
        )
        
        console.print("Enter transformation requests. Type 'exit' to quit.")
        console.print("Type 'help' for additional commands.")
        
        while True:
            # Get user input
            request = Prompt.ask("\n👤 Enter transformation request")
            
            # Check for special commands
            if request.lower() == 'exit':
                console.print("Exiting interactive mode")
                break
            elif request.lower() == 'help':
                show_help_menu()
                continue
            elif request.lower() == 'tables':
                show_tables(agent)
                continue
            
            # Process the transformation request
            console.print(Panel.fit("Processing", style="blue"))
            result = agent.process_request(request)
            
            if result.success:
                console.print(Panel.fit("Success", style="green"))
                display_result(result)
                
                # Ask for confirmation
                confirmed = Confirm.ask("Is this transformation correct? (y/n)")
                agent.confirm_result(confirmed)
                
                # If the user said no, they're likely to refine the request next
                if not confirmed:
                    console.print("[yellow]Please provide your refinement request for this transformation.[/yellow]")
            else:
                console.print(Panel.fit("Transformation failed", style="red"))
                if result and result.error:
                    console.print(f"Error: {result.error}")
    
    except Exception as e:
        console.print(f"[red]Error in interactive mode: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
    finally:
        # Stop Spark session
        if 'agent' in locals():
            agent.shutdown()
            console.print("Interactive mode ended.")


def get_postgres_config(pg_host=None, pg_port=None, pg_db=None, pg_user=None, pg_pass=None) -> Dict[str, Any]:
    """
    Get PostgreSQL configuration from parameters or interactive input.
    
    Args:
        pg_host: PostgreSQL host
        pg_port: PostgreSQL port
        pg_db: PostgreSQL database name
        pg_user: PostgreSQL username
        pg_pass: PostgreSQL password
        
    Returns:
        Dict with PostgreSQL configuration
    """
    # Use environment variables as defaults
    pg_host = pg_host or os.environ.get("POSTGRES_HOST")
    pg_port = pg_port or os.environ.get("POSTGRES_PORT", 5432)
    pg_db = pg_db or os.environ.get("POSTGRES_DB")
    pg_user = pg_user or os.environ.get("POSTGRES_USER", "postgres")
    pg_pass = pg_pass or os.environ.get("POSTGRES_PASSWORD", "postgres")
    
    # If any required values are missing, prompt the user
    if not all([pg_host, pg_port, pg_db]):
        console.print("Some database connection details missing. Starting interactive discovery...")
        
        # Discovery mode
        return interactive_db_discovery()
    
    # Return configuration
    return {
        "host": pg_host,
        "port": int(pg_port),
        "database": pg_db,
        "user": pg_user,
        "password": pg_pass
    }


def interactive_db_discovery() -> Dict[str, Any]:
    """
    Interactive PostgreSQL discovery.
    
    Returns:
        Dict with PostgreSQL configuration
    """
    console.print(Panel.fit("Discovering PostgreSQL connections...", style="blue"))
    
    # Discover PostgreSQL servers
    discovery = DatabaseDiscovery()
    servers = discovery.discover_postgresql_servers()
    
    if not servers:
        console.print("[yellow]No PostgreSQL servers discovered. You'll need to enter details manually.[/yellow]")
        servers = ["localhost", "127.0.0.1"]
    
    # Let user select a server
    console.print("Discovered PostgreSQL servers:")
    for i, server in enumerate(servers, 1):
        console.print(f"  {i}. {server}")
    
    selected_idx = Prompt.ask("Select server (or enter custom host)", default="1")
    try:
        host = servers[int(selected_idx) - 1]
    except (ValueError, IndexError):
        host = selected_idx
    
    # Get port
    port = Prompt.ask("PostgreSQL port", default="5432")
    
    # Get credentials
    user = Prompt.ask("PostgreSQL username", default="postgres")
    password = Prompt.ask("PostgreSQL password", default="postgres", password=True)
    
    # Test connection
    console.print(f"Connecting to PostgreSQL server at {host}:{port}...")
    
    # Get available databases
    try:
        # Create a temporary config for listing databases
        temp_config = {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password
        }
        
        databases = discovery.list_databases(temp_config)
        
        if not databases:
            console.print("[yellow]No databases found. You'll need to enter the database name manually.[/yellow]")
            database = Prompt.ask("PostgreSQL database name")
        else:
            console.print("\nAvailable databases:")
            for i, db in enumerate(databases, 1):
                console.print(f"  {i}. {db}")
            
            selected_idx = Prompt.ask("Select database (or enter custom database)", default="1")
            try:
                database = databases[int(selected_idx) - 1]
            except (ValueError, IndexError):
                database = selected_idx
        
        # Test the connection
        console.print(f"Testing connection to {host}:{port}/{database}...")
        
        # Create final config
        config = {
            "host": host,
            "port": int(port),
            "database": database,
            "user": user,
            "password": password
        }
        
        return config
        
    except Exception as e:
        console.print(f"[red]Error during database discovery: {str(e)}[/red]")
        
        # Fallback to manual entry
        database = Prompt.ask("PostgreSQL database name", default="postgres")
        
        return {
            "host": host,
            "port": int(port),
            "database": database,
            "user": user,
            "password": password
        }


def display_result(result) -> None:
    """
    Display execution result in a formatted table.
    
    Args:
        result: Execution result object
    """
    if not result or not result.success:
        console.print("[red]No valid result to display[/red]")
        return
    
    # Get result data from PySpark DataFrame
    if hasattr(result.result_data, "toPandas"):
        try:
            # Check row count first - do this before limiting the data!
            total_rows = result.row_count
            if not total_rows and hasattr(result.result_data, "count"):
                try:
                    total_rows = result.result_data.count()
                except:
                    pass
            
            # Try to convert to Pandas for display
            pdf = result.result_data.limit(10).toPandas()
            
            # Create a table to display the results
            table = Table(title="Result Preview (First 10 rows)")
            
            # Add columns
            for column in pdf.columns:
                table.add_column(str(column))
            
            # Add rows
            for _, row in pdf.iterrows():
                table.add_row(*[str(value) for value in row.values])
            
            # Show the table
            console.print(table)
            
            # Show row count
            console.print(f"Total rows: {total_rows if total_rows else 'Unknown'}")
            return
        except Exception as e:
            console.print(f"[yellow]Error converting to pandas: {str(e)}[/yellow]")
    
    # Fallback: Try to get raw data
    if hasattr(result.result_data, "collect"):
        try:
            # Check row count first - do this before limiting the data!
            total_rows = result.row_count
            if not total_rows and hasattr(result.result_data, "count"):
                try:
                    total_rows = result.result_data.count()
                except:
                    pass
                    
            # Collect rows for display
            rows = result.result_data.limit(10).collect()
            
            if not rows:
                console.print("[yellow]Result is empty (no rows)[/yellow]")
                return
                
            # Create a table to display the results
            table = Table(title="Result Preview (First 10 rows)")
            
            # Add columns
            for field in result.result_data.schema.fields:
                table.add_column(field.name)
            
            # Add rows
            for row in rows:
                table.add_row(*[str(row[field.name]) for field in result.result_data.schema.fields])
            
            # Show the table
            console.print(table)
            
            # Show row count
            console.print(f"Total rows: {total_rows if total_rows else 'Unknown'}")
            return
        except Exception as e:
            console.print(f"[yellow]Error collecting rows: {str(e)}[/yellow]")
    
    # Last resort fallback
    console.print("[yellow]Unable to display result data in table format[/yellow]")
    console.print(f"Result type: {type(result.result_data)}")
    console.print(f"Result: {result.result_data}")
    console.print(f"Total rows: {result.row_count if hasattr(result, 'row_count') and result.row_count else 'Unknown'}")


def show_help_menu() -> None:
    """Show help menu for interactive mode."""
    console.print(Panel.fit("SparkPG Agent Help", style="blue"))
    console.print("Available commands:")
    console.print("  exit     - Exit interactive mode")
    console.print("  help     - Show this help menu")
    console.print("  tables   - Show available tables")
    console.print("\nAny other input will be treated as a transformation request.")


def show_tables(agent) -> None:
    """
    Show available tables in the database.
    
    Args:
        agent: TransformationAgent instance
    """
    try:
        tables = agent.schema_memory.get_all_table_names()
        
        if not tables:
            console.print("[yellow]No tables found in the database.[/yellow]")
            return
        
        console.print(Panel.fit("Available Tables", style="blue"))
        
        for table in sorted(tables):
            console.print(f"- {table}")
            
            # Show columns if available
            columns = agent.schema_memory.get_table_columns(table)
            if columns:
                for col in columns:
                    col_type = agent.schema_memory.get_column_type(table, col)
                    console.print(f"  • {col}: {col_type}")
                console.print("")
    
    except Exception as e:
        console.print(f"[red]Error retrieving tables: {str(e)}[/red]")


@cli.command()
def start_dashboard():
    """Start the AgentTrace dashboard for visualizing traces."""
    import os
    import subprocess
    import sys
    
    agenttrace_path = os.path.expanduser("~/.postgres_spark_agent/agenttrace")
    
    # Check if AgentTrace repository exists
    if not os.path.exists(agenttrace_path):
        console.print("[red]Error: AgentTrace repository not found.[/red]")
        console.print("Please run the post-installation script:")
        console.print("  pip install -e .")
        console.print("Or clone it manually:")
        console.print("  git clone https://github.com/tensorstax/agenttrace.git ~/.postgres_spark_agent/agenttrace")
        console.print("  cd ~/.postgres_spark_agent/agenttrace/frontend")
        console.print("  npm run install:all")
        return
    
    # Start the dashboard
    console.print(Panel.fit("Starting AgentTrace Dashboard", style="blue"))
    console.print("This will start both the API server and the web interface.")
    console.print("[yellow]Press Ctrl+C to stop the dashboard.[/yellow]")
    
    try:
        # Change directory to the frontend directory
        os.chdir(os.path.join(agenttrace_path, "frontend"))
        
        # Start the dashboard
        console.print("[green]Starting dashboard...[/green]")
        subprocess.run(["npm", "run", "start"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting dashboard: {e}[/red]")
    except KeyboardInterrupt:
        console.print("[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main() 
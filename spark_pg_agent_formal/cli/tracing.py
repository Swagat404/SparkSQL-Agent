"""
Tracing dashboard for Spark PG Agent.
"""
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def start_dashboard():
    """Start the AgentTrace dashboard."""
    console.print(Panel("Starting AgentTrace dashboard...", title="AgentTrace", border_style="cyan"))
    
    # Check if npm is installed
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error:[/red] npm is not installed. Please install Node.js and npm to use the dashboard.")
        return
    
    # Try to find the agenttrace frontend directory
    paths_to_check = [
        # Check if we're in a development environment
        Path("./frontend"),
        # Check the package installation directory
        Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "frontend",
        # Check site-packages agenttrace
        Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "agenttrace" / "frontend"
    ]
    
    frontend_dir = None
    for path in paths_to_check:
        if path.exists() and (path / "package.json").exists():
            frontend_dir = path
            break
    
    if frontend_dir is None:
        console.print("[red]Error:[/red] Could not find AgentTrace frontend directory.")
        console.print("You can install agenttrace manually: pip install agenttrace")
        console.print("Then run: agenttrace start")
        return
    
    # Start the dashboard in a separate process
    console.print(f"Found AgentTrace frontend at: {frontend_dir}")
    console.print("Starting dashboard server...")
    
    dashboard_process = subprocess.Popen(
        ["npm", "run", "start"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for the server to start
    time.sleep(3)
    
    # Check if the process is still running
    if dashboard_process.poll() is not None:
        console.print("[red]Error:[/red] Failed to start dashboard server.")
        stdout, stderr = dashboard_process.communicate()
        console.print(f"Output: {stdout}")
        console.print(f"Error: {stderr}")
        return
    
    # Open the dashboard in a browser
    url = "http://localhost:5173"
    console.print(f"Opening dashboard at [blue]{url}[/blue]")
    webbrowser.open(url)
    
    # Keep the server running until interrupted
    try:
        console.print("[yellow]Dashboard server is running. Press Ctrl+C to stop.[/yellow]")
        while True:
            line = dashboard_process.stdout.readline()
            if not line:
                break
            console.print(f"[dim]{line.strip()}[/dim]")
    except KeyboardInterrupt:
        console.print("[yellow]Stopping dashboard server...[/yellow]")
    finally:
        dashboard_process.terminate()
        dashboard_process.wait()
        console.print("[green]Dashboard server stopped.[/green]")
        
    console.print(Panel("AgentTrace dashboard closed", title="AgentTrace", border_style="cyan")) 
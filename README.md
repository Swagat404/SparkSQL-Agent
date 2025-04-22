# Spark PostgreSQL Agent

An autonomous agent for natural language transformations on PostgreSQL and MySQL databases using Apache Spark.

## Features

- Transform natural language requests into executable PySpark code
- Autonomous error detection and self-correction
- Multi-phase compilation for reliable code generation
- Interactive mode for exploration and iterative development
- Context awareness for multi-step workflows
- Validation of transformation results
- Web-based interface with user authentication
- Multiple database support (PostgreSQL and MySQL)
- Automatic visualization suggestions
- Result caching for improved performance
- Feedback collection for ongoing improvement

## Requirements

To run this application, you'll need:

- Docker Engine - version 19.03.0 or higher
- Docker Compose - version 1.27.0 or higher
- OpenAI API key or Anthropic API key

## Installation

### Installing Docker
On Ubuntu/Debian:

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

On macOS:

- Download and install Docker Desktop from https://www.docker.com/products/docker-desktop/
- Docker Compose is included with Docker Desktop for macOS

On Windows:

- Download and install Docker Desktop from https://www.docker.com/products/docker-desktop/
- Ensure WSL 2 is installed and configured (Docker Desktop will guide you through this)
  Docker Compose is included with Docker Desktop for Windows

### Verifying Installation
Verify that Docker and Docker Compose are properly installed:

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version
```

## Running the Application

### Setting Up Environment Variables

Create a `.env` file in the root directory with your API keys and database connection details:

```
# PostgreSQL Connection
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MySQL Connection (new in Version 1)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DB=testdb
MYSQL_USER=mysql
MYSQL_PASSWORD=mysql

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Feature Flags
VALIDATION_ENABLED=true
VISUALIZATION_ENABLED=true
CACHE_ENABLED=true

# JWT Secret for authentication
JWT_SECRET_KEY=your_secret_key_change_in_production
```

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/yourusername/SparkSQL-Agent.git
cd SparkSQL-Agent

# Build and start all services
docker-compose up -d

# Check the status of the containers
docker-compose ps
```

### Accessing the Application

- **Web Interface**: Open your browser and navigate to http://localhost:3000
- **Backend API**: Available at http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Web Application (New in Version 1)

The web application provides the following features:

- **User Authentication**: Secure login and authentication system
- **Database Connection Management**: Connect to PostgreSQL and MySQL databases
- **Query Interface**: Enter natural language queries and see results
- **Data Visualization**: Automatically generated charts based on query results
- **Error Analysis**: View and analyze query failures
- **Feedback Collection**: Submit feedback for failed queries

### Default Login Credentials

- Username: admin
- Password: password123

**Important**: Change these credentials before deploying to production.

## Using the CLI Interface

The CLI interface is still available for users who prefer command-line interaction:

```bash
# Access the PySpark container
docker exec -it sparksql-agent-pyspark-1 bash

# Run the CLI in interactive mode
python -m spark_pg_agent_formal.cli interactive

# Or with explicit database connection
python -m spark_pg_agent_formal.cli interactive --pg-host postgres --pg-port 5432 --pg-db postgres
```

## Example Queries

### Simple Queries

```
> Show me the top 10 customers by total orders
> List all products with price greater than 50
> Calculate average order value by month
```

### Complex Transformations

```
> Join orders and customers tables, group by customer country, and show average order value
> Find customers who bought product X but not product Y
> Calculate month-over-month growth in sales for each product category
```

### Multi-Step Workflows

```
> Show me sales by region
> Now filter to just the last quarter
> Compare that with the same quarter last year
> Calculate the percentage change
```

## Database Support

Version 1 supports the following databases:

- **PostgreSQL**: Full support for schema extraction and querying
- **MySQL**: Full support for schema extraction and querying

## Visualizations

The agent can automatically suggest appropriate visualizations for query results, including:

- Bar charts
- Line charts
- Pie charts
- Scatter plots
- Histograms

## Architecture

The Spark PostgreSQL Agent is structured in multiple layers:

```
+--------------------------------------------------------------+
|                 Spark PostgreSQL Agent Architecture           |
+--------------------------------------------------------------+
                            |
              +-------------v------------+    +----------------+
              |    Interface Layer       |<-->|   Web/CLI      |
              +-------------------------+     +----------------+
                          |
+--------------------------------------------------------------+
|                       Core Layer                              |
|                                                               |
|   +-------------------+        +---------------------+        |
|   |TransformationAgent|<------>|    AgentMemory      |        |
|   +-------------------+        +---------------------+        |
|       |       |       |                                       |
|       |       |       v                                       |
|       |       |  +------------+                               |
|       |       |  |SchemaMemory|                               |
|       |       |  +------------+                               |
|       |       |       ^                                       |
|       |       v       |                                       |
|       |  +------------+                                       |
|       |  |DatabaseMgr |                                       |
|       |  +------------+                                       |
|       v                                                       |
|  +---------------------------+                                |
|  |   MultiPhaseLLMCompiler   |                               |
|  |---------------------------|                                |
|  | +------------+ +--------+ |  +-----------+ +------------+ |
|  | |schema_     | |plan_   | |  |SparkExec. | |ResultValid.| |
|  | |analysis    | |gen     | |  +-----------+ +------------+ |
|  | +------------+ +--------+ |                                |
|  | +------------+ +--------+ |  +-----------+ +------------+ |
|  | |code_       | |code_   | |  |ResultCache| |Visualization| |
|  | |generation  | |review  | |  +-----------+ +------------+ |
|  | +------------+ +--------+ |                                |
|  +---------------------------+                                |
|                                                               |
+--------------------------------------------------------------+
                 |                         ^
                 v                         |
+--------------------------------------------------------------+
|                     External Systems                          |
|  +-------------+  +-------------+  +----------------------+   |
|  |  Database   |  | Spark       |  | LLM Services         |   |
|  |  (PG/MySQL) |  | Cluster     |  | (OpenAI, Anthropic)  |   |
|  +-------------+  +-------------+  +----------------------+   |
+--------------------------------------------------------------+
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

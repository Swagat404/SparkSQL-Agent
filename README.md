# Spark PostgreSQL Agent

An autonomous agent for natural language transformations on PostgreSQL databases using Apache Spark.

## Features

- Transform natural language requests into executable PySpark code
- Autonomous error detection and self-correction
- Multi-phase compilation for reliable code generation
- Interactive mode for exploration and iterative development
- Context awareness for multi-step workflows
- Validation of transformation results

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spark_pg_agent_formal.git
cd spark_pg_agent_formal

# Install the package
pip install -e .
```

## Requirements

- Python 3.8+
- Apache Spark 3.1+
- PostgreSQL server
- OpenAI API key or Anthropic API key

## Environment Setup

Create a `.env` file with your API keys and database connection details:

```
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# PostgreSQL connection details (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## Usage

### Interactive Mode

```bash
# Start the interactive mode
python -m spark_pg_agent_formal.cli interactive

# Or with explicit database connection
python -m spark_pg_agent_formal.cli interactive --pg-host localhost --pg-port 5432 --pg-db your_database
```

### Single Command Execution

```bash
# Execute a specific transformation
python -m spark_pg_agent_formal.cli execute "show me total sales by region"
```

## Example Workflows

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

## Architecture

The agent architecture follows these key principles:

1. **State Management**: Tracking the agent's state through the transformation process
2. **Multi-phase Compilation**: Breaking down the code generation into discrete phases
3. **Result Detection**: Intelligently identifying the result DataFrame in the executed code
4. **Error Recovery**: Sequential recovery pipeline for handling errors
5. **Memory System**: Tracking context across multiple transformation steps

## Extending

To add new capabilities:

1. **Add new recovery strategies**: Extend the error recovery pipeline in the agent
2. **Enhance schema understanding**: Improve the schema memory system
3. **Add visualization features**: Implement new visualization capabilities for results

## License

MIT 
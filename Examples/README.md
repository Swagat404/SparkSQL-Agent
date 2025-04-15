# Spark PostgreSQL Agent Examples

This directory contains example scripts demonstrating how to use the Spark PostgreSQL Agent for data transformation tasks.

## Examples

### Quick Start

The `quickstart.py` script provides a minimal example to get started with the Spark PostgreSQL Agent. It demonstrates how to:

- Initialize the TransformationAgent with the required configuration
- Execute a simple natural language query
- Display and save the results

```bash
# Run the quickstart example
python Examples/quickstart.py
```

### Basic Transformation

The `basic_transformation.py` script shows how to perform a basic data transformation using the Spark PostgreSQL Agent. It demonstrates:

- Configuring the agent with custom settings
- Running a specific transformation query
- Handling various types of outputs (text, dataframe, visualization)

```bash
# Run the basic transformation example
python Examples/basic_transformation.py
```

## Environment Setup

Before running the examples, make sure to set up your environment:

1. Create a `.env` file with your PostgreSQL and OpenAI API credentials
2. Install the required dependencies

Example `.env` file:
```
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=your_database
PG_USER=your_username
PG_PASSWORD=your_password
OPENAI_API_KEY=your_openai_api_key
```

## Adding More Examples

Feel free to add more example scripts to demonstrate additional functionality:

- Advanced visualizations
- Complex SQL transformations
- Custom schema inference
- Performance optimization techniques 
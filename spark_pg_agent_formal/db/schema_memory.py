"""
Schema memory for the Spark PostgreSQL Agent.

This module provides database schema tracking and management capabilities.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from spark_pg_agent_formal.tracing import disable_console_output
import os

# Disable tracing output
disable_console_output()

# Also set environment variable to disable AgentTrace spinners
os.environ["AGENTTRACE_NO_SPINNER"] = "1"

class TableSchema(BaseModel):
    """Schema information for a database table"""
    name: str
    columns: Dict[str, str]  # column_name -> data_type
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: Dict[str, Tuple[str, str]] = Field(default_factory=dict)  # column -> (referenced_table, referenced_column)


class SchemaMemory:
    """
    Stores and provides access to database schema information.
    Provides a unified schema representation for both PostgreSQL and MySQL.
    """
    
    def __init__(self):
        """Initialize the schema memory."""
        self.table_schemas = {}  # Dict[table_name, column_list]
        self.relationships = []  # List of foreign key relationships
        self.indexes = []  # List of indexes
    
    def add_table_schema(self, table_name: str, columns: List[Dict[str, Any]]) -> None:
        """
        Add a table schema to memory.
        
        Args:
            table_name: The name of the table
            columns: List of column objects with metadata
        """
        self.table_schemas[table_name] = columns
    
    def add_relationship(
        self, table: str, column: str, foreign_table: str, foreign_column: str
    ) -> None:
        """
        Add a foreign key relationship to memory.
        
        Args:
            table: The table with the foreign key
            column: The column containing the foreign key
            foreign_table: The referenced table
            foreign_column: The referenced column
        """
        self.relationships.append({
            "table": table,
            "column": column,
            "foreign_table": foreign_table,
            "foreign_column": foreign_column
        })
    
    def add_index(self, table: str, column: str, is_unique: bool = False) -> None:
        """
        Add an index to memory.
        
        Args:
            table: The table with the index
            column: The indexed column
            is_unique: Whether the index is unique
        """
        self.indexes.append({
            "table": table,
            "column": column,
            "is_unique": is_unique
        })
    
    def get_all_table_names(self) -> List[str]:
        """Get a list of all table names."""
        return list(self.table_schemas.keys())
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all columns for a specific table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of column objects with metadata
        """
        return self.table_schemas.get(table_name, [])
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get all column names for a specific table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of column names
        """
        columns = self.get_table_columns(table_name)
        return [col["name"] for col in columns]
    
    def get_relationships_for_table(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get all relationships where the given table is either the source or target.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of relationship objects
        """
        return [
            rel for rel in self.relationships 
            if rel["table"] == table_name or rel["foreign_table"] == table_name
        ]
    
    def get_indexes_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all indexes for a specific table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of index objects
        """
        return [idx for idx in self.indexes if idx["table"] == table_name]
    
    def table_has_column(self, table_name: str, column_name: str) -> bool:
        """
        Check if a table has a specific column.
        
        Args:
            table_name: The name of the table
            column_name: The name of the column
            
        Returns:
            True if the column exists in the table, False otherwise
        """
        columns = self.get_column_names(table_name)
        return column_name in columns
    
    def get_column_data_type(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get the data type of a specific column.
        
        Args:
            table_name: The name of the table
            column_name: The name of the column
            
        Returns:
            The data type of the column, or None if not found
        """
        columns = self.get_table_columns(table_name)
        for col in columns:
            if col["name"] == column_name:
                return col["data_type"]
        return None
    
    def get_related_tables(self, table_name: str) -> Set[str]:
        """
        Get all tables that are directly related to the given table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            Set of related table names
        """
        related_tables = set()
        for rel in self.relationships:
            if rel["table"] == table_name:
                related_tables.add(rel["foreign_table"])
            elif rel["foreign_table"] == table_name:
                related_tables.add(rel["table"])
        return related_tables
    
    def get_schema_summary(self) -> str:
        """
        Get a human-readable summary of the entire schema.
        
        Returns:
            A string summarizing the schema
        """
        summary = []
        
        # Add tables and columns
        summary.append(f"Database contains {len(self.table_schemas)} tables:")
        for table_name, columns in self.table_schemas.items():
            column_str = ", ".join([f"{col['name']} ({col['data_type']})" for col in columns])
            summary.append(f"- {table_name}: {column_str}")
        
        # Add relationships
        if self.relationships:
            summary.append("\nRelationships:")
            for rel in self.relationships:
                summary.append(
                    f"- {rel['table']}.{rel['column']} -> "
                    f"{rel['foreign_table']}.{rel['foreign_column']}"
                )
        
        # Add indexes
        if self.indexes:
            summary.append("\nIndexes:")
            for idx in self.indexes:
                unique_str = "UNIQUE " if idx["is_unique"] else ""
                summary.append(f"- {unique_str}INDEX on {idx['table']}.{idx['column']}")
        
        return "\n".join(summary)
    
    def get_spark_schema_mapping(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get a mapping of table schemas in a format suitable for PySpark.
        
        Returns:
            A dictionary mapping table names to column definitions for PySpark
        """
        spark_mapping = {}
        
        # Map SQL data types to PySpark data types
        type_mapping = {
            # PostgreSQL types
            "integer": "IntegerType",
            "bigint": "LongType",
            "smallint": "ShortType",
            "character varying": "StringType",
            "varchar": "StringType",
            "text": "StringType",
            "timestamp without time zone": "TimestampType",
            "timestamp with time zone": "TimestampType",
            "date": "DateType",
            "boolean": "BooleanType",
            "numeric": "DecimalType",
            "decimal": "DecimalType",
            "real": "FloatType",
            "double precision": "DoubleType",
            "json": "StringType",
            "jsonb": "StringType",
            
            # MySQL types
            "int": "IntegerType",
            "tinyint": "ShortType",
            "bigint": "LongType",
            "float": "FloatType",
            "double": "DoubleType",
            "char": "StringType",
            "varchar": "StringType",
            "tinytext": "StringType",
            "text": "StringType",
            "longtext": "StringType",
            "datetime": "TimestampType",
            "timestamp": "TimestampType",
            "date": "DateType",
            "time": "TimestampType",
            "year": "IntegerType",
            "enum": "StringType",
            "set": "StringType",
            "blob": "BinaryType",
            "longblob": "BinaryType",
            "mediumblob": "BinaryType",
            "tinyblob": "BinaryType"
        }
        
        for table_name, columns in self.table_schemas.items():
            spark_columns = []
            for col in columns:
                # Get the mapped PySpark type or default to StringType
                base_type = col["data_type"].lower()
                spark_type = type_mapping.get(base_type, "StringType")
                
                # Handle decimal types with precision and scale
                if base_type in ("numeric", "decimal"):
                    # Default precision and scale if not specified
                    precision = 38
                    scale = 18
                    
                    spark_type = f"DecimalType({precision}, {scale})"
                
                spark_columns.append({
                    "name": col["name"],
                    "type": spark_type,
                    "nullable": col["is_nullable"]
                })
            
            spark_mapping[table_name] = spark_columns
        
        return spark_mapping 
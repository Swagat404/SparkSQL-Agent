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


class SchemaMemory(BaseModel):
    """Memory system for tracking database schema information"""
    
    # Store table schemas by name
    tables: Dict[str, TableSchema] = Field(default_factory=dict)
    
    def add_table_schema(self, table_schema: TableSchema) -> None:
        """
        Add a table schema to memory.
        
        Args:
            table_schema: The table schema to add
        """
        self.tables[table_schema.name] = table_schema
    
    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """
        Get schema information for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            TableSchema if the table exists, None otherwise
        """
        return self.tables.get(table_name)
    
    def get_all_table_names(self) -> List[str]:
        """
        Get all table names in the schema.
        
        Returns:
            List of table names
        """
        return list(self.tables.keys())
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Get column names for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of column names if the table exists, empty list otherwise
        """
        table = self.get_table_schema(table_name)
        if table:
            return list(table.columns.keys())
        return []
    
    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Get the data type of a column.
        
        Args:
            table_name: The name of the table
            column_name: The name of the column
            
        Returns:
            Data type if the column exists, None otherwise
        """
        table = self.get_table_schema(table_name)
        if table and column_name in table.columns:
            return table.columns[column_name]
        return None
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """
        Get primary keys for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of primary key columns if the table exists, empty list otherwise
        """
        table = self.get_table_schema(table_name)
        if table:
            return table.primary_keys
        return []
    
    def get_foreign_keys(self, table_name: str) -> Dict[str, Tuple[str, str]]:
        """
        Get foreign keys for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            Dictionary mapping column names to (referenced_table, referenced_column) if the table exists,
            empty dict otherwise
        """
        table = self.get_table_schema(table_name)
        if table:
            return table.foreign_keys
        return {}
    
    def get_related_tables(self, table_name: str) -> List[str]:
        """
        Get tables related to the given table through foreign keys.
        
        Args:
            table_name: The name of the table
            
        Returns:
            List of related table names
        """
        related_tables = set()
        
        # Tables that this table references
        table = self.get_table_schema(table_name)
        if table:
            for referenced_table, _ in table.foreign_keys.values():
                related_tables.add(referenced_table)
        
        # Tables that reference this table
        for other_table_name, other_table in self.tables.items():
            for referenced_table, _ in other_table.foreign_keys.values():
                if referenced_table == table_name:
                    related_tables.add(other_table_name)
        
        # Return as list, excluding the original table
        return [t for t in related_tables if t != table_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert schema memory to a dictionary.
        
        Returns:
            Dictionary representation of the schema memory
        """
        return {
            "tables": {name: table.dict() for name, table in self.tables.items()}
        }
    
    def format_schema_for_prompt(self) -> str:
        """
        Format schema information for inclusion in a prompt.
        
        Returns:
            Formatted schema information string
        """
        if not self.tables:
            return "No schema information available."
        
        schema_str = "Database Schema:\n"
        
        for table_name, table in self.tables.items():
            schema_str += f"Table: {table_name}\n"
            schema_str += "  Columns:\n"
            
            for col_name, col_type in table.columns.items():
                pk_indicator = " (PK)" if col_name in table.primary_keys else ""
                fk_info = ""
                if col_name in table.foreign_keys:
                    ref_table, ref_col = table.foreign_keys[col_name]
                    fk_info = f" (FK -> {ref_table}.{ref_col})"
                schema_str += f"    {col_name}: {col_type}{pk_indicator}{fk_info}\n"
            
            schema_str += "\n"
        
        return schema_str 
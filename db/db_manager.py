"""
Database manager for the Spark PostgreSQL Agent.

This module handles database connections, schema extraction, and query execution.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List, Optional, Tuple
import socket
import re

from spark_pg_agent_formal.db.schema_memory import SchemaMemory, TableSchema


class DatabaseManager:
    """Database connection and schema management"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with PostgreSQL connection details.
        
        Args:
            config: Dictionary with host, port, database, user, password keys
        """
        self.config = config
        self.connection = None
        self.schema_memory = SchemaMemory()
    
    def connect(self) -> bool:
        """
        Connect to the PostgreSQL database.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                database=self.config.get("database", "postgres"),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", "postgres")
            )
            return True
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection works, False otherwise
        """
        try:
            if not self.connection:
                self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone()[0] == 1
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
    
    def load_schema(self) -> bool:
        """
        Load database schema information into schema memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connection:
                self.connect()
            
            # Get a list of tables
            tables = self._get_tables()
            
            # Populate schema memory
            for table_name in tables:
                schema = self._get_table_schema(table_name)
                if schema:
                    self.schema_memory.add_table_schema(schema)
            
            return True
        except Exception as e:
            print(f"Error loading schema: {str(e)}")
            return False
    
    def _get_tables(self) -> List[str]:
        """
        Get list of tables in the current database.
        
        Returns:
            List of table names
        """
        tables = []
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            for row in cursor:
                tables.append(row[0])
                
        return tables
    
    def _get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """
        Get schema information for a table.
        
        Args:
            table_name: The name of the table
            
        Returns:
            TableSchema if successful, None otherwise
        """
        try:
            # Get column information
            columns = {}
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                for row in cursor:
                    columns[row[0]] = row[1]
            
            # Get primary key information
            primary_keys = []
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                      AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                    WHERE constraint_type = 'PRIMARY KEY' AND tc.table_name = %s
                """, (table_name,))
                
                for row in cursor:
                    primary_keys.append(row[0])
            
            # Get foreign key information
            foreign_keys = {}
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM
                        information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
                """, (table_name,))
                
                for row in cursor:
                    foreign_keys[row[0]] = (row[1], row[2])
            
            # Create and return TableSchema
            return TableSchema(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys
            )
                
        except Exception as e:
            print(f"Error getting schema for table {table_name}: {str(e)}")
            return None
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample data from a table.
        
        Args:
            table_name: The name of the table
            limit: Maximum number of rows to return
            
        Returns:
            List of dictionaries with sample data
        """
        try:
            if not self.connection:
                self.connect()
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting sample data from {table_name}: {str(e)}")
            return []
    
    def get_schema_memory(self) -> SchemaMemory:
        """
        Get the schema memory.
        
        Returns:
            SchemaMemory instance
        """
        return self.schema_memory


class DatabaseDiscovery:
    """PostgreSQL server discovery and connection utilities"""
    
    @staticmethod
    def discover_postgresql_servers() -> List[str]:
        """
        Discover PostgreSQL servers on localhost and common ports.
        
        Returns:
            List of discovered PostgreSQL servers
        """
        servers = []
        
        # Common hosts to check
        hosts = ["localhost", "127.0.0.1"]
        
        # Add the current machine's hostname
        try:
            hosts.append(socket.gethostname())
        except:
            pass
        
        # Check PostgreSQL on common ports
        ports = [5432, 5433]
        
        for host in hosts:
            for port in ports:
                if DatabaseDiscovery._check_postgres_port(host, port):
                    servers.append(host)
                    break  # Once we find a working port for this host, move on
        
        return servers
    
    @staticmethod
    def _check_postgres_port(host: str, port: int) -> bool:
        """
        Check if PostgreSQL is running on the specified host and port.
        
        Args:
            host: Hostname to check
            port: Port to check
            
        Returns:
            True if PostgreSQL appears to be running, False otherwise
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((host, port))
            s.close()
            return True
        except:
            return False
    
    @staticmethod
    def list_databases(config: Dict[str, Any]) -> List[str]:
        """
        List available databases on a PostgreSQL server.
        
        Args:
            config: Connection configuration with host, port, user, password
            
        Returns:
            List of database names
        """
        try:
            # Create a connection to the postgres database first
            temp_config = config.copy()
            temp_config["database"] = "postgres"  # Connect to default postgres database
            
            conn = psycopg2.connect(
                host=temp_config.get("host", "localhost"),
                port=temp_config.get("port", 5432),
                database=temp_config.get("database", "postgres"),
                user=temp_config.get("user", "postgres"),
                password=temp_config.get("password", "postgres")
            )
            
            databases = []
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                for row in cursor:
                    databases.append(row[0])
            
            conn.close()
            return databases
            
        except Exception as e:
            print(f"Error listing databases: {str(e)}")
            return [] 
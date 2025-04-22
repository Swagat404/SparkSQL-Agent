import os
import psycopg2
import mysql.connector
from typing import Optional, Dict, List, Any, Tuple
from .schema_memory import SchemaMemory

class DatabaseManager:
    """Manages database connections and schema extraction for different database types."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        dbname: str = None,
        user: str = None,
        password: str = None,
        db_type: str = "postgresql"  # "postgresql" or "mysql"
    ):
        """Initialize the database manager with connection parameters."""
        # Load from environment variables if not provided
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.dbname = dbname or os.getenv("POSTGRES_DB", "postgres")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.db_type = db_type.lower()
        
        self.conn = None
        self.connection_string = self._get_connection_string()
    
    def _get_connection_string(self) -> str:
        """Get the connection string for logging purposes."""
        if self.db_type == "postgresql":
            return f"postgresql://{self.user}:***@{self.host}:{self.port}/{self.dbname}"
        elif self.db_type == "mysql":
            return f"mysql://{self.user}:***@{self.host}:{self.port}/{self.dbname}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def connect(self) -> None:
        """Connect to the database."""
        try:
            if self.db_type == "postgresql":
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password
                )
            elif self.db_type == "mysql":
                self.conn = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.dbname,
                    user=self.user,
                    password=self.password
                )
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            
            print(f"Connected to {self.db_type} database at {self.host}:{self.port}/{self.dbname}")
        except Exception as e:
            print(f"Error connecting to {self.db_type} database: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print(f"Disconnected from {self.db_type} database")
    
    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
    
    def _get_postgres_tables(self) -> List[str]:
        """Get all table names from PostgreSQL database."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
        
        return tables
    
    def _get_mysql_tables(self) -> List[str]:
        """Get all table names from MySQL database."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.dbname,))
            tables = [row[0] for row in cursor.fetchall()]
        
        return tables
    
    def _get_postgres_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a PostgreSQL table."""
        query = """
        SELECT 
            column_name, 
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM 
            information_schema.columns
        WHERE 
            table_schema = 'public' 
            AND table_name = %s
        ORDER BY 
            ordinal_position;
        """
        
        columns = []
        with self.conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            for row in cursor.fetchall():
                column = {
                    "name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4]
                }
                columns.append(column)
        
        return columns
    
    def _get_mysql_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a MySQL table."""
        query = """
        SELECT 
            column_name, 
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM 
            information_schema.columns
        WHERE 
            table_schema = %s 
            AND table_name = %s
        ORDER BY 
            ordinal_position;
        """
        
        columns = []
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.dbname, table_name))
            for row in cursor.fetchall():
                column = {
                    "name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4]
                }
                columns.append(column)
        
        return columns
    
    def _get_postgres_foreign_keys(self) -> List[Dict[str, str]]:
        """Get foreign key relationships from PostgreSQL database."""
        query = """
        SELECT
            tc.table_name AS table_name, 
            kcu.column_name AS column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public';
        """
        
        foreign_keys = []
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                fk = {
                    "table": row[0],
                    "column": row[1],
                    "foreign_table": row[2],
                    "foreign_column": row[3]
                }
                foreign_keys.append(fk)
        
        return foreign_keys
    
    def _get_mysql_foreign_keys(self) -> List[Dict[str, str]]:
        """Get foreign key relationships from MySQL database."""
        query = """
        SELECT
            TABLE_NAME AS table_name,
            COLUMN_NAME AS column_name,
            REFERENCED_TABLE_NAME AS foreign_table_name,
            REFERENCED_COLUMN_NAME AS foreign_column_name
        FROM
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE
            REFERENCED_TABLE_SCHEMA = %s
            AND REFERENCED_TABLE_NAME IS NOT NULL;
        """
        
        foreign_keys = []
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.dbname,))
            for row in cursor.fetchall():
                fk = {
                    "table": row[0],
                    "column": row[1],
                    "foreign_table": row[2],
                    "foreign_column": row[3]
                }
                foreign_keys.append(fk)
        
        return foreign_keys
    
    def _get_postgres_indexes(self) -> List[Dict[str, Any]]:
        """Get index information from PostgreSQL database."""
        query = """
        SELECT
            t.relname AS table_name,
            i.relname AS index_name,
            a.attname AS column_name,
            ix.indisunique AS is_unique
        FROM
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
        WHERE
            t.oid = ix.indrelid
            AND i.oid = ix.indexrelid
            AND a.attrelid = t.oid
            AND a.attnum = ANY(ix.indkey)
            AND t.relkind = 'r'
            AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        ORDER BY
            t.relname,
            i.relname;
        """
        
        indexes = []
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                index = {
                    "table": row[0],
                    "index_name": row[1],
                    "column": row[2],
                    "is_unique": row[3]
                }
                indexes.append(index)
        
        return indexes
    
    def _get_mysql_indexes(self) -> List[Dict[str, Any]]:
        """Get index information from MySQL database."""
        query = """
        SELECT
            TABLE_NAME AS table_name,
            INDEX_NAME AS index_name,
            COLUMN_NAME AS column_name,
            NOT NON_UNIQUE AS is_unique
        FROM
            INFORMATION_SCHEMA.STATISTICS
        WHERE
            TABLE_SCHEMA = %s
        ORDER BY
            table_name,
            index_name;
        """
        
        indexes = []
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.dbname,))
            for row in cursor.fetchall():
                index = {
                    "table": row[0],
                    "index_name": row[1],
                    "column": row[2],
                    "is_unique": row[3]
                }
                indexes.append(index)
        
        return indexes
    
    def load_schema(self, schema_memory: SchemaMemory) -> None:
        """Load database schema into schema memory."""
        try:
            self.connect()
            
            # Get table list based on database type
            if self.db_type == "postgresql":
                tables = self._get_postgres_tables()
                foreign_keys = self._get_postgres_foreign_keys()
                indexes = self._get_postgres_indexes()
            elif self.db_type == "mysql":
                tables = self._get_mysql_tables()
                foreign_keys = self._get_mysql_foreign_keys()
                indexes = self._get_mysql_indexes()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            
            # Process each table
            for table_name in tables:
                # Get columns based on database type
                if self.db_type == "postgresql":
                    columns = self._get_postgres_table_columns(table_name)
                elif self.db_type == "mysql":
                    columns = self._get_mysql_table_columns(table_name)
                
                # Store table schema in memory
                schema_memory.add_table_schema(table_name, columns)
            
            # Store relationships
            for fk in foreign_keys:
                schema_memory.add_relationship(
                    fk["table"], 
                    fk["column"], 
                    fk["foreign_table"], 
                    fk["foreign_column"]
                )
            
            # Store indexes
            for idx in indexes:
                schema_memory.add_index(
                    idx["table"],
                    idx["column"],
                    idx["is_unique"]
                )
            
            print(f"Loaded schema for {len(tables)} tables")
        except Exception as e:
            print(f"Error loading schema: {str(e)}")
            raise
        finally:
            self.disconnect() 
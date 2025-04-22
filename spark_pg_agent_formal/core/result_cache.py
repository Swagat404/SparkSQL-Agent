import os
import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

class ResultCache:
    """
    Cache for storing and retrieving query results to improve performance.
    """
    
    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600):
        """
        Initialize the result cache.
        
        Args:
            cache_dir: Directory to store cache files (default: .cache)
            ttl_seconds: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), ".cache")
        self.ttl_seconds = ttl_seconds
        self.memory_cache = {}  # For fast in-memory access
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _generate_key(self, query: str, db_config: Dict[str, Any]) -> str:
        """
        Generate a unique key for the query and database configuration.
        
        Args:
            query: The natural language query
            db_config: Database configuration (connection details)
            
        Returns:
            A unique hash key
        """
        # Create a string to hash that includes the query and relevant db config
        hash_input = f"{query}|{db_config.get('type', '')}|{db_config.get('host', '')}|{db_config.get('database', '')}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _get_cache_file_path(self, key: str) -> str:
        """
        Get the file path for a cache entry.
        
        Args:
            key: The cache key
            
        Returns:
            Path to the cache file
        """
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, query: str, db_config: Dict[str, Any]) -> Optional[Tuple[pd.DataFrame, str, float]]:
        """
        Get cached result for a query.
        
        Args:
            query: The natural language query
            db_config: Database configuration
            
        Returns:
            Tuple of (result_dataframe, generated_code, execution_time) if cache hit,
            None if cache miss or entry expired
        """
        key = self._generate_key(query, db_config)
        
        # First check in-memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            timestamp = cache_entry.get("timestamp", 0)
            
            # Check if entry has expired
            if time.time() - timestamp <= self.ttl_seconds:
                print(f"Cache hit for query: {query[:30]}...")
                
                # Return the cached result
                result_df = pd.DataFrame(cache_entry["result"])
                return result_df, cache_entry["code"], cache_entry["execution_time"]
            else:
                # Entry expired, remove from memory cache
                del self.memory_cache[key]
        
        # Check file cache if not in memory or if memory entry expired
        cache_file = self._get_cache_file_path(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                timestamp = cache_entry.get("timestamp", 0)
                
                # Check if entry has expired
                if time.time() - timestamp <= self.ttl_seconds:
                    print(f"File cache hit for query: {query[:30]}...")
                    
                    # Load into memory cache for faster access next time
                    self.memory_cache[key] = cache_entry
                    
                    # Return the cached result
                    result_df = pd.DataFrame(cache_entry["result"])
                    return result_df, cache_entry["code"], cache_entry["execution_time"]
                else:
                    # Entry expired, remove the file
                    os.remove(cache_file)
            except Exception as e:
                print(f"Error reading cache file: {str(e)}")
                # Remove corrupt cache file
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        
        # Cache miss or expired entry
        return None
    
    def set(self, query: str, db_config: Dict[str, Any], result: pd.DataFrame, 
            code: str, execution_time: float) -> None:
        """
        Store result in cache.
        
        Args:
            query: The natural language query
            db_config: Database configuration
            result: DataFrame result
            code: Generated PySpark code
            execution_time: Execution time in seconds
        """
        key = self._generate_key(query, db_config)
        
        # Convert DataFrame to JSON-serializable format
        result_dict = result.to_dict(orient="records") if not result.empty else []
        
        # Create cache entry
        cache_entry = {
            "query": query,
            "result": result_dict,
            "code": code,
            "execution_time": execution_time,
            "timestamp": time.time(),
            "db_type": db_config.get("type", "unknown")
        }
        
        # Store in memory cache
        self.memory_cache[key] = cache_entry
        
        # Store in file cache
        cache_file = self._get_cache_file_path(key)
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f)
            print(f"Cached result for query: {query[:30]}...")
        except Exception as e:
            print(f"Error writing to cache file: {str(e)}")
    
    def invalidate(self, query: str = None, db_config: Dict[str, Any] = None) -> None:
        """
        Invalidate cache entries.
        
        Args:
            query: The natural language query (if None, invalidate all entries for the db_config)
            db_config: Database configuration (if None, invalidate all entries)
        """
        if query and db_config:
            # Invalidate specific entry
            key = self._generate_key(query, db_config)
            
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from file cache
            cache_file = self._get_cache_file_path(key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
        
        elif db_config:
            # Invalidate all entries for this database
            db_type = db_config.get("type", "")
            db_host = db_config.get("host", "")
            db_name = db_config.get("database", "")
            
            # Remove from memory cache
            for key in list(self.memory_cache.keys()):
                entry = self.memory_cache[key]
                if (entry.get("db_type") == db_type and 
                    db_host in entry.get("query", "") and
                    db_name in entry.get("query", "")):
                    del self.memory_cache[key]
            
            # This is a best-effort approach for file cache
            # A more precise approach would require indexing
            for file_name in os.listdir(self.cache_dir):
                try:
                    if file_name.endswith(".json"):
                        file_path = os.path.join(self.cache_dir, file_name)
                        with open(file_path, 'r') as f:
                            entry = json.load(f)
                        
                        if (entry.get("db_type") == db_type and 
                            db_host in entry.get("query", "") and
                            db_name in entry.get("query", "")):
                            os.remove(file_path)
                except Exception as e:
                    print(f"Error processing cache file {file_name}: {str(e)}")
        
        else:
            # Invalidate all entries
            self.memory_cache.clear()
            
            # Remove all cache files
            for file_name in os.listdir(self.cache_dir):
                if file_name.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, file_name))
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        current_time = time.time()
        
        # Clean up memory cache
        for key in list(self.memory_cache.keys()):
            entry = self.memory_cache[key]
            if current_time - entry.get("timestamp", 0) > self.ttl_seconds:
                del self.memory_cache[key]
                count += 1
        
        # Clean up file cache
        for file_name in os.listdir(self.cache_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(self.cache_dir, file_name)
                try:
                    with open(file_path, 'r') as f:
                        entry = json.load(f)
                    
                    if current_time - entry.get("timestamp", 0) > self.ttl_seconds:
                        os.remove(file_path)
                        count += 1
                except Exception as e:
                    # Remove corrupt cache files
                    os.remove(file_path)
                    count += 1
                    print(f"Removed corrupt cache file {file_name}: {str(e)}")
        
        return count 
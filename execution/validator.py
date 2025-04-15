"""
Result validation module for Spark PostgreSQL Agent.

This module provides functionality for validating transformation results.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
from spark_pg_agent_formal.execution.executor import ExecutionResult


class ValidationError(Exception):
    """Exception raised for validation errors"""
    pass


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, valid: bool, errors: List[str] = None, warnings: List[str] = None):
        """
        Initialize the validation result.
        
        Args:
            valid: Whether the validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    @property
    def has_errors(self) -> bool:
        """Whether the validation has errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Whether the validation has warnings"""
        return len(self.warnings) > 0
    
    def __str__(self) -> str:
        """String representation of the validation result"""
        if self.valid:
            if self.has_warnings:
                return f"Valid with {len(self.warnings)} warnings"
            return "Valid"
        return f"Invalid with {len(self.errors)} errors"


class ResultValidator:
    """
    Validates transformation results for correctness.
    
    This class handles:
    1. Schema validation
    2. Result integrity checks
    3. Business logic validation
    """
    
    def validate(self, result: ExecutionResult, schema_memory=None) -> ValidationResult:
        """
        Validate a transformation result.
        
        Args:
            result: Execution result object
            schema_memory: Optional schema memory for schema validation
            
        Returns:
            ValidationResult indicating success or failure
        """
        # Initialize validation result
        errors = []
        warnings = []
        
        # Check if execution was successful
        if not result.success:
            errors.append(f"Execution failed: {result.error or 'Unknown error'}")
            return ValidationResult(valid=False, errors=errors)
        
        # Check if result data is present
        if result.result_data is None:
            errors.append("No result data found in execution result")
            return ValidationResult(valid=False, errors=errors)
        
        # Validate DataFrame result
        if hasattr(result.result_data, "dtypes"):
            # It's a PySpark DataFrame
            try:
                if result.row_count == 0:
                    warnings.append("Result data is empty (zero rows)")
            except Exception as e:
                errors.append(f"Error validating PySpark DataFrame: {str(e)}")
        else:
            # Not a recognized result type
            errors.append(f"Result data is not a recognized DataFrame type: {type(result.result_data)}")
        
        # Determine if validation passed
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    # Keeping the older method for backwards compatibility
    def validate_result(self, result: Dict[str, Any], schema_memory=None) -> ValidationResult:
        """
        Validate a transformation result in the old dictionary format.
        
        Args:
            result: Execution result dictionary
            schema_memory: Optional schema memory for schema validation
            
        Returns:
            ValidationResult indicating success or failure
        """
        # Initialize validation result
        errors = []
        warnings = []
        
        # Check if execution was successful
        if not result.get("success", False):
            errors.append(f"Execution failed: {result.get('error', 'Unknown error')}")
            return ValidationResult(valid=False, errors=errors)
        
        # Check if result data is present
        result_data = result.get("result")
        if result_data is None:
            errors.append("No result data found in execution result")
            return ValidationResult(valid=False, errors=errors)
        
        # Validate result data structure
        if not isinstance(result_data, list):
            errors.append(f"Expected result data to be a list, got {type(result_data)}")
            return ValidationResult(valid=False, errors=errors)
        
        # Validate result data contents
        if len(result_data) == 0:
            warnings.append("Result data is empty (zero rows)")
        
        # Validate result schema if available
        schema = result.get("schema")
        if schema and schema_memory:
            schema_errors = self._validate_schema(schema, schema_memory)
            errors.extend(schema_errors)
        
        # Determine if validation passed
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    def _validate_schema(self, schema_str: str, schema_memory) -> List[str]:
        """
        Validate a result schema against the known database schema.
        
        Args:
            schema_str: Schema string from the result
            schema_memory: Schema memory with database schema information
            
        Returns:
            List of error messages (empty if validation passed)
        """
        # Basic implementation - could be enhanced with more sophisticated schema validation
        errors = []
        
        # TODO: Implement schema validation if needed
        
        return errors
    
    def extract_result_schema(self, result_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract schema information from result data.
        
        Args:
            result_data: List of result records
            
        Returns:
            Dictionary mapping column names to type information
        """
        if not result_data:
            return {}
        
        schema = {}
        
        # Use the first row to determine schema
        first_row = result_data[0]
        
        for col_name, value in first_row.items():
            nullable = False
            
            # Determine type
            if value is None:
                data_type = "unknown"
                nullable = True
            elif isinstance(value, int):
                data_type = "int"
            elif isinstance(value, float):
                data_type = "float"
            elif isinstance(value, str):
                data_type = "str"
            elif isinstance(value, bool):
                data_type = "bool"
            elif isinstance(value, (list, tuple)):
                data_type = "array"
            elif isinstance(value, dict):
                data_type = "object"
            else:
                data_type = str(type(value))
            
            # Check for NULL values in other rows
            if not nullable:
                for row in result_data[1:]:
                    if row.get(col_name) is None:
                        nullable = True
                        break
            
            schema[col_name] = {
                "type": data_type,
                "nullable": nullable
            }
        
        return schema 
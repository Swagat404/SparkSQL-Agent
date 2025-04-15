"""
LLM provider implementations for Spark PostgreSQL Agent.

This module provides abstractions for different LLM providers (OpenAI, Anthropic).
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json

# Try to import required packages, gracefully handle if not available
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def get_completion(self, prompt: str) -> str:
        """
        Get a completion from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Completion string from the LLM
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: Optional API key (uses OPENAI_API_KEY env var if not provided)
            model: Model to use (default: gpt-4o)
        """
        if not openai:
            raise ImportError("The 'openai' package is required for OpenAIProvider")
        
        # Use provided API key or get from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it directly or set OPENAI_API_KEY environment variable.")
        
        # Set API key on the client
        openai.api_key = self.api_key
        
        # Set model
        self.model = model
    
    def get_completion(self, prompt: str) -> str:
        """
        Get a completion from OpenAI.
        
        Args:
            prompt: The prompt to send to the OpenAI API
            
        Returns:
            Completion from the OpenAI API
        """
        try:
            # Create a chat completion
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert data analyst and PySpark developer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Lower temperature for more deterministic outputs
            )
            
            # Extract and return the response content
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Optional API key (uses ANTHROPIC_API_KEY env var if not provided)
            model: Model to use (default: claude-3-opus-20240229)
        """
        if not anthropic:
            raise ImportError("The 'anthropic' package is required for AnthropicProvider")
        
        # Use provided API key or get from environment variable
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Provide it directly or set ANTHROPIC_API_KEY environment variable.")
        
        # Create client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Set model
        self.model = model
    
    def get_completion(self, prompt: str) -> str:
        """
        Get a completion from Anthropic Claude.
        
        Args:
            prompt: The prompt to send to the Anthropic API
            
        Returns:
            Completion from the Anthropic API
        """
        try:
            # Create a message
            response = self.client.messages.create(
                model=self.model,
                system="You are an expert data analyst and PySpark developer.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Lower temperature for more deterministic outputs
            )
            
            # Extract and return the response content
            return response.content[0].text
            
        except Exception as e:
            print(f"Error calling Anthropic API: {str(e)}")
            raise


def get_provider(provider_name: str = "openai", api_key: Optional[str] = None) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider_name: Name of the provider (openai/anthropic)
        api_key: Optional API key
        
    Returns:
        LLMProvider instance
    """
    if provider_name.lower() == "openai":
        return OpenAIProvider(api_key=api_key)
    elif provider_name.lower() == "anthropic":
        return AnthropicProvider(api_key=api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}") 
"""
OpenAI API Helper - Provides unified interface for OpenAI API calls
Compatible with openai>=1.0.0
"""

import os
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
import structlog

logger = structlog.get_logger(__name__)


class OpenAIHelper:
    """Helper class for OpenAI API interactions using the new client-based API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI helper.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    def is_configured(self) -> bool:
        """Check if OpenAI API is properly configured."""
        return self.client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create a chat completion using OpenAI API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Dictionary with response data or None if API is not configured
        """
        if not self.is_configured():
            logger.warning("OpenAI API not configured, skipping chat completion")
            return None
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Convert response to dictionary format similar to old API
            return {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            }
        
        except Exception as e:
            logger.error("Error calling OpenAI API", error=str(e))
            raise
    
    async def get_completion_text(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[str]:
        """
        Get just the text content from a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Response text or None if API is not configured or call fails
        """
        response = await self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        if response and response.get("choices"):
            return response["choices"][0]["message"]["content"]
        
        return None


# Global instance for convenience
_global_helper: Optional[OpenAIHelper] = None


def get_openai_helper() -> OpenAIHelper:
    """Get or create the global OpenAI helper instance."""
    global _global_helper
    if _global_helper is None:
        _global_helper = OpenAIHelper()
    return _global_helper


async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for chat completion using global helper.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model to use (default: gpt-3.5-turbo)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-2)
        **kwargs: Additional parameters to pass to the API
    
    Returns:
        Dictionary with response data or None if API is not configured
    """
    helper = get_openai_helper()
    return await helper.chat_completion(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )


async def get_completion_text(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    **kwargs
) -> Optional[str]:
    """
    Convenience function to get just the text from a chat completion.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model to use (default: gpt-3.5-turbo)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-2)
        **kwargs: Additional parameters to pass to the API
    
    Returns:
        Response text or None if API is not configured or call fails
    """
    helper = get_openai_helper()
    return await helper.get_completion_text(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )


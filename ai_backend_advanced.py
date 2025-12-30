"""
Advanced AI Backend - Enhanced LLM integration with advanced features
Includes fine-tuning support, caching, context awareness, and streaming
"""

import asyncio
import json
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime, timedelta
from functools import lru_cache
import os

from jarvis.logger import get_logger
from jarvis.ai_backend import AIBackend, AIProvider

logger = get_logger(__name__)


class CachedResponse:
    """Cache entry for AI responses"""

    def __init__(self, query: str, response: Dict[str, Any], ttl_seconds: int = 3600):
        """
        Initialize cached response
        
        Args:
            query: Original query
            response: Response data
            ttl_seconds: Time-to-live in seconds
        """
        self.query = query.lower().strip()
        self.response = response
        self.created_at = datetime.now()
        self.ttl = timedelta(seconds=ttl_seconds)

    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        return datetime.now() < self.created_at + self.ttl


class ResponseCache:
    """
    Simple in-memory response cache
    Reduces API calls for repeated queries
    """

    def __init__(self, max_entries: int = 100):
        """
        Initialize response cache
        
        Args:
            max_entries: Maximum cache entries
        """
        self.cache: Dict[str, CachedResponse] = {}
        self.max_entries = max_entries

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response
        
        Args:
            query: Query string
        
        Returns:
            Cached response or None
        """
        key = query.lower().strip()
        
        if key in self.cache:
            cached = self.cache[key]
            if cached.is_valid():
                logger.info(f"Cache hit for query: {query}")
                return cached.response
            else:
                # Remove expired entry
                del self.cache[key]
        
        return None

    def set(self, query: str, response: Dict[str, Any], ttl: int = 3600) -> None:
        """
        Set cached response
        
        Args:
            query: Query string
            response: Response data
            ttl: Time-to-live in seconds
        """
        # Remove oldest entry if cache is full
        if len(self.cache) >= self.max_entries:
            oldest_key = min(self.cache.keys(),
                            key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]

        key = query.lower().strip()
        self.cache[key] = CachedResponse(query, response, ttl)
        logger.info(f"Cached response for: {query}")

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'max_entries': self.max_entries,
            'valid_entries': sum(1 for c in self.cache.values() if c.is_valid()),
        }


class ContextManager:
    """
    Manages conversation context and history
    Provides context for multi-turn conversations
    """

    def __init__(self, max_history: int = 10):
        """
        Initialize context manager
        
        Args:
            max_history: Maximum history entries to keep
        """
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.user_info: Dict[str, Any] = {}

    def add_turn(self, user_input: str, assistant_response: str) -> None:
        """
        Add conversation turn to history
        
        Args:
            user_input: User's message
            assistant_response: Assistant's response
        """
        turn = {
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'assistant': assistant_response,
        }
        
        self.history.append(turn)
        
        # Remove oldest entry if exceeded
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_context(self) -> str:
        """
        Get formatted context for conversation
        
        Returns:
            Formatted context string
        """
        if not self.history:
            return "No previous context"

        context_lines = []
        for turn in self.history[-3:]:  # Last 3 turns
            context_lines.append(f"User: {turn['user']}")
            context_lines.append(f"Assistant: {turn['assistant']}")

        return "\n".join(context_lines)

    def set_user_info(self, key: str, value: Any) -> None:
        """Set user information"""
        self.user_info[key] = value

    def get_user_info(self, key: str) -> Optional[Any]:
        """Get user information"""
        return self.user_info.get(key)

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.history.clear()

    def get_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.history.copy()


class AdvancedAIBackend(AIBackend):
    """
    Advanced AI Backend with caching, context, and streaming
    Extends the basic AIBackend with additional features
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize advanced AI backend
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.cache = ResponseCache(max_entries=config.get('cache_size', 100) if config else 100)
        self.context = ContextManager(max_history=config.get('history_size', 10) if config else 10)
        self.enable_cache = config.get('features', {}).get('response_caching', True) if config else True
        self.enable_context = config.get('features', {}).get('conversation_context', True) if config else True

    def query_sync(self, query: str, use_cache: bool = True, include_context: bool = True) -> Optional[Dict[str, Any]]:
        """
        Synchronous query with caching and context support
        
        Args:
            query: User query
            use_cache: Use cached responses
            include_context: Include conversation context
        
        Returns:
            Response dictionary or None
        """
        # Check cache
        if use_cache and self.enable_cache:
            cached = self.cache.get(query)
            if cached:
                return cached

        # Prepare query with context
        enhanced_query = query
        if include_context and self.enable_context:
            context = self.context.get_context()
            if context != "No previous context":
                enhanced_query = f"Context: {context}\n\nNew question: {query}"

        # Query AI
        response = super().query_sync(enhanced_query)

        if response and self.enable_cache:
            self.cache.set(query, response)
            self.context.add_turn(query, response.get('text', ''))

        return response

    async def query_async(self, query: str, use_cache: bool = True,
                         include_context: bool = True) -> Optional[Dict[str, Any]]:
        """
        Asynchronous query with caching and context
        
        Args:
            query: User query
            use_cache: Use cached responses
            include_context: Include conversation context
        
        Returns:
            Response dictionary or None
        """
        # Check cache
        if use_cache and self.enable_cache:
            cached = self.cache.get(query)
            if cached:
                return cached

        # Query AI
        response = await super().query_async(query)

        if response and self.enable_cache:
            self.cache.set(query, response)
            self.context.add_turn(query, response.get('text', ''))

        return response

    async def stream_query(self, query: str) -> AsyncIterator[str]:
        """
        Stream query response
        
        Args:
            query: User query
        
        Yields:
            Response chunks
        """
        try:
            if not self.provider:
                logger.error("No AI provider configured")
                return

            # For basic providers that don't support streaming
            response = await self.query_async(query, use_cache=False)
            if response:
                yield response.get('text', '')
            
        except Exception as e:
            logger.error(f"Stream query error: {e}")
            yield f"Error: {str(e)}"

    def get_response_with_alternatives(self, query: str, num_alternatives: int = 3) -> List[Dict[str, Any]]:
        """
        Get multiple response options (simulated)
        
        Args:
            query: User query
            num_alternatives: Number of alternatives to generate
        
        Returns:
            List of response alternatives
        """
        # Basic implementation: return main response
        response = self.query_sync(query)
        
        if response:
            return [response] * min(num_alternatives, 1)
        return []

    def fine_tune_response(self, query: str, response: str, feedback: str) -> None:
        """
        Record feedback for response fine-tuning
        (Placeholder for future implementation)
        
        Args:
            query: Original query
            response: Assistant response
            feedback: User feedback (positive/negative/neutral)
        """
        logger.info(f"Feedback recorded - Query: {query}, Feedback: {feedback}")
        # Could save to file/database for future analysis

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.context.get_history()

    def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.context.clear_history()
        logger.info("Conversation cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        return {
            'cache': self.get_cache_stats(),
            'history_length': len(self.context.history),
            'provider': self.provider.__class__.__name__ if self.provider else None,
        }

    def set_user_preference(self, key: str, value: Any) -> None:
        """Set user preference"""
        self.context.set_user_info(key, value)
        logger.info(f"User preference set: {key} = {value}")

    def get_user_preference(self, key: str) -> Optional[Any]:
        """Get user preference"""
        return self.context.get_user_info(key)


class StreamingAdapter:
    """
    Adapter for streaming responses from non-streaming providers
    """

    def __init__(self, text: str, chunk_size: int = 50):
        """
        Initialize streaming adapter
        
        Args:
            text: Text to stream
            chunk_size: Size of each chunk
        """
        self.text = text
        self.chunk_size = chunk_size
        self.position = 0

    async def stream(self) -> AsyncIterator[str]:
        """
        Stream text in chunks
        
        Yields:
            Text chunks
        """
        while self.position < len(self.text):
            chunk = self.text[self.position:self.position + self.chunk_size]
            yield chunk
            self.position += self.chunk_size
            await asyncio.sleep(0.05)  # Simulate streaming delay


class BatchQueryProcessor:
    """
    Process multiple queries in batch
    """

    def __init__(self, ai_backend: AdvancedAIBackend):
        """
        Initialize batch processor
        
        Args:
            ai_backend: AI backend instance
        """
        self.ai = ai_backend

    async def process_batch(self, queries: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Process multiple queries concurrently
        
        Args:
            queries: List of queries
        
        Returns:
            List of responses
        """
        tasks = [self.ai.query_async(q) for q in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def process_batch_sync(self, queries: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Process multiple queries synchronously
        
        Args:
            queries: List of queries
        
        Returns:
            List of responses
        """
        return [self.ai.query_sync(q) for q in queries]
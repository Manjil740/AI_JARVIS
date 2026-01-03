"""
COMPLETE CODE - jarvis/ai_backend.py
This is the FULL updated file with all the new imports and modifications
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from typing import Dict, Any, Optional
from datetime import datetime
import json

from jarvis.logger import get_logger
from jarvis.utils import load_config

# ✅ NEW IMPORTS: Smart routing and response customization
from smart_router import SmartRouter
from response_customizer import ResponseCustomizer

logger = get_logger(__name__)


class AIBackend:
    """
    AI Backend with smart routing and response customization
    Routes queries to best provider and customizes responses
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize AI backend with smart routing and customization
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        
        # ✅ NEW: Smart routing and response customization
        self.router = SmartRouter(self.config)
        self.customizer = ResponseCustomizer(self.config)
        
        # Existing configuration
        self.current_provider = self.config.get('ai', {}).get('default_provider', 'gemini')
        self.openai_key = self.config.get('api_keys', {}).get('openai')
        self.gemini_key = self.config.get('api_keys', {}).get('gemini')
        self.deepseek_key = self.config.get('api_keys', {}).get('deepseek')
        
        # Provider endpoints
        self.providers = {
            'openai': {
                'base_url': 'https://api.openai.com/v1/chat/completions',
                'model': self.config.get('ai', {}).get('providers', {}).get('openai', {}).get('model', 'gpt-4'),
            },
            'gemini': {
                'base_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                'model': 'gemini-pro',
            },
            'deepseek': {
                'base_url': 'https://api.deepseek.com/v1/chat/completions',
                'model': self.config.get('ai', {}).get('providers', {}).get('deepseek', {}).get('model', 'deepseek-coder'),
            },
        }
        
        # Session tracking
        self.last_query = None
        self.last_response = None
        self.query_history = []
        self.max_history = 50
        
        self.logger.info(f"AIBackend initialized with provider: {self.current_provider}")
        self.logger.info("Smart routing enabled")
        self.logger.info("Response customization enabled")

    def query_sync(self, query: str, provider: Optional[str] = None) -> str:
        """
        Query AI with smart routing and response customization
        
        Args:
            query: Query string
            provider: Optional provider override (defaults to smart routing)
        
        Returns:
            Customized response string
        """
        try:
            self.logger.info(f"Processing query: {query[:50]}...")
            
            # ✅ NEW: Smart routing (auto-select best provider)
            if provider is None and self.config.get('ai', {}).get('smart_routing', True):
                provider, task_type = self.router.route_query(query)
                self.logger.info(f"Smart routing selected: {provider} for task: {task_type.value}")
            else:
                provider = provider or self.current_provider
                self.logger.info(f"Using provider: {provider}")
            
            # Store for later use
            self.current_provider = provider
            self.last_query = query
            
            # Call the appropriate provider
            response = self._query_provider(provider, query)
            
            if not response:
                self.logger.error(f"Empty response from {provider}")
                return "No response received"
            
            # Extract text from response if it's a dict
            if isinstance(response, dict):
                response_text = response.get('text', response.get('content', str(response)))
            else:
                response_text = str(response)
            
            # ✅ NEW: Customize response based on user preferences
            task_type_str = str(task_type) if 'task_type' in locals() else 'general'
            customized = self.customizer.customize_response(
                response_text,
                task_type=task_type_str
            )
            
            # Store in history
            self.last_response = customized
            self._add_to_history(query, customized, provider)
            
            return customized
            
        except Exception as e:
            self.logger.error(f"Query error: {e}", exc_info=True)
            return f"Error processing query: {str(e)}"

    def _query_provider(self, provider: str, query: str) -> str:
        """
        Query specific provider
        
        Args:
            provider: Provider name (openai, gemini, deepseek)
            query: Query string
        
        Returns:
            Response from provider
        """
        try:
            self.logger.info(f"Querying {provider}: {query[:50]}...")
            
            if provider == 'openai':
                return self._query_openai(query)
            elif provider == 'gemini':
                return self._query_gemini(query)
            elif provider == 'deepseek':
                return self._query_deepseek(query)
            else:
                self.logger.error(f"Unknown provider: {provider}")
                return None
                
        except Exception as e:
            self.logger.error(f"Provider query error ({provider}): {e}", exc_info=True)
            return None

    def _query_openai(self, query: str) -> Dict[str, Any]:
        """
        Query OpenAI API
        
        Args:
            query: Query string
        
        Returns:
            Response dictionary or None
        """
        if not self.openai_key:
            self.logger.error("OpenAI API key not configured")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_key}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'model': self.providers['openai']['model'],
                'messages': [
                    {'role': 'user', 'content': query}
                ],
                'temperature': 0.7,
                'max_tokens': 2000,
            }
            
            response = requests.post(
                self.providers['openai']['base_url'],
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['choices'][0]['message']['content']
                return {'text': text, 'provider': 'openai'}
            else:
                self.logger.error(f"OpenAI API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"OpenAI query error: {e}")
            return None

    def _query_gemini(self, query: str) -> Dict[str, Any]:
        """
        Query Google Gemini API
        
        Args:
            query: Query string
        
        Returns:
            Response dictionary or None
        """
        if not self.gemini_key:
            self.logger.error("Gemini API key not configured")
            return None
        
        try:
            url = f"{self.providers['gemini']['base_url']}?key={self.gemini_key}"
            
            data = {
                'contents': [
                    {
                        'parts': [
                            {'text': query}
                        ]
                    }
                ],
                'generationConfig': {
                    'temperature': 0.7,
                    'maxOutputTokens': 2000,
                }
            }
            
            response = requests.post(
                url,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                return {'text': text, 'provider': 'gemini'}
            else:
                self.logger.error(f"Gemini API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Gemini query error: {e}")
            return None

    def _query_deepseek(self, query: str) -> Dict[str, Any]:
        """
        Query DeepSeek API
        
        Args:
            query: Query string
        
        Returns:
            Response dictionary or None
        """
        if not self.deepseek_key:
            self.logger.error("DeepSeek API key not configured")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.deepseek_key}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'model': self.providers['deepseek']['model'],
                'messages': [
                    {'role': 'user', 'content': query}
                ],
                'temperature': 0.7,
                'max_tokens': 2000,
            }
            
            response = requests.post(
                self.providers['deepseek']['base_url'],
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['choices'][0]['message']['content']
                return {'text': text, 'provider': 'deepseek'}
            else:
                self.logger.error(f"DeepSeek API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"DeepSeek query error: {e}")
            return None

    def _add_to_history(self, query: str, response: str, provider: str) -> None:
        """
        Add query and response to history
        
        Args:
            query: Query string
            response: Response string
            provider: Provider used
        """
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'response': response[:500],  # Store first 500 chars
                'provider': provider,
            }
            
            self.query_history.append(entry)
            
            # Keep only last N items
            if len(self.query_history) > self.max_history:
                self.query_history = self.query_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"History error: {e}")

    def get_history(self, limit: int = 10) -> list:
        """
        Get query history
        
        Args:
            limit: Number of entries to return
        
        Returns:
            List of history entries
        """
        return self.query_history[-limit:] if self.query_history else []

    def clear_history(self) -> None:
        """Clear query history"""
        self.query_history = []
        self.logger.info("Query history cleared")

    def set_provider(self, provider: str) -> bool:
        """
        Set default provider
        
        Args:
            provider: Provider name
        
        Returns:
            Boolean indicating success
        """
        if provider in self.providers:
            self.current_provider = provider
            self.logger.info(f"Provider set to: {provider}")
            return True
        else:
            self.logger.error(f"Unknown provider: {provider}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get AI backend status
        
        Returns:
            Status dictionary
        """
        return {
            'current_provider': self.current_provider,
            'smart_routing_enabled': self.config.get('ai', {}).get('smart_routing', True),
            'response_customization_enabled': True,
            'providers_available': list(self.providers.keys()),
            'query_count': len(self.query_history),
            'last_query': self.last_query,
            'last_provider_used': self.current_provider,
        }


def main():
    """Test AI backend"""
    config = load_config()
    backend = AIBackend(config)
    
    # Test query
    test_queries = [
        "research machine learning",
        "write python code for fibonacci",
        "solve this math problem: 2+2=?",
        "create a creative story",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = backend.query_sync(query)
        print(f"Response: {response[:100]}...")
        print(f"Provider: {backend.current_provider}")


if __name__ == "__main__":
    main()
"""
Smart AI Provider Router - Automatically selects best AI provider for each task
Routes queries to optimal provider based on task type
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import re
from jarvis.logger import get_logger

logger = get_logger(__name__)


class TaskType(Enum):
    """Task type categories"""
    RESEARCH = "research"
    CODE = "code"
    MATH = "math"
    CREATIVE = "creative"
    FACTUAL = "factual"
    SYSTEM = "system"
    GENERAL = "general"


class SmartRouter:
    """
    Intelligent router that selects the best AI provider for each task
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize smart router
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.smart_routing_enabled = self.config.get('ai', {}).get('smart_routing', True)
        
        # Default provider mapping
        self.provider_mapping = self.config.get('ai', {}).get('provider_mapping', {
            "research": "gemini",
            "code": "openai",
            "math": "deepseek",
            "creative": "openai",
            "factual": "gemini",
            "system": "deepseek",
            "default": "gemini"
        })
        
        # Task detection patterns
        self.task_patterns = {
            TaskType.RESEARCH: [
                r'research|find|search|look up|investigate|explore|discover|learn about',
                r'what\'?s? the latest|recent|current|up to date',
                r'tell me about|information about|facts about',
            ],
            TaskType.CODE: [
                r'code|write|implement|function|class|script|program|snippet',
                r'how to.*python|javascript|java|c\+\+|rust|go',
                r'solve.*problem|algorithm|data structure',
            ],
            TaskType.MATH: [
                r'calculate|solve|equation|integral|derivative|matrix|algebra|geometry',
                r'math|formula|proof|theorem|logic|reasoning',
                r'what\'?s? ?\d+\s*[\+\-\*/]|calculus|linear algebra',
            ],
            TaskType.CREATIVE: [
                r'write|story|poem|song|creative|fiction|imagine|invent',
                r'description|narrative|dialogue|script|play',
                r'make.*funny|joke|pun|humorous',
            ],
            TaskType.FACTUAL: [
                r'fact|true|history|biography|definition|who|what is|explain',
                r'when|where|how many|population|capital|president',
                r'definition of|meaning of|do you know',
            ],
            TaskType.SYSTEM: [
                r'system|command|shell|terminal|execute|run|install|configure',
                r'sudo|root|permission|access|security|firewall',
                r'linux|ubuntu|debian|fedora|arch',
            ],
        }

    def detect_task_type(self, query: str) -> TaskType:
        """
        Detect task type from query
        
        Args:
            query: User query string
        
        Returns:
            TaskType enum value
        """
        query_lower = query.lower()
        
        # Score each task type
        scores = {}
        
        for task_type, patterns in self.task_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            scores[task_type] = score
        
        # Return highest scored task type
        if max(scores.values()) > 0:
            best_task = max(scores, key=scores.get)
            logger.info(f"Detected task type: {best_task.value}")
            return best_task
        
        logger.info("No specific task type detected, using general")
        return TaskType.GENERAL

    def get_provider_for_task(self, task_type: TaskType) -> str:
        """
        Get best provider for task type
        
        Args:
            task_type: TaskType enum value
        
        Returns:
            Provider name string
        """
        if not self.smart_routing_enabled:
            return self.provider_mapping.get("default", "gemini")
        
        provider = self.provider_mapping.get(task_type.value, 
                                            self.provider_mapping.get("default", "gemini"))
        
        logger.info(f"Selected provider '{provider}' for task type '{task_type.value}'")
        return provider

    def route_query(self, query: str) -> Tuple[str, TaskType]:
        """
        Route query to best provider
        
        Args:
            query: User query string
        
        Returns:
            Tuple of (provider_name, task_type)
        """
        # Detect task type
        task_type = self.detect_task_type(query)
        
        # Get provider for this task
        provider = self.get_provider_for_task(task_type)
        
        return provider, task_type

    def format_reasoning(self, query: str, task_type: TaskType, provider: str) -> str:
        """
        Format explanation of routing decision
        
        Args:
            query: User query
            task_type: Detected task type
            provider: Selected provider
        
        Returns:
            Formatted reasoning string
        """
        provider_descriptions = {
            "openai": "OpenAI GPT-4 (expert code generation & creative writing)",
            "deepseek": "DeepSeek (strong reasoning & math capabilities)",
            "gemini": "Google Gemini (web search & factual information)",
            "custom": "Custom endpoint"
        }
        
        reason = f"""
Task Analysis:
├─ Type Detected: {task_type.value.upper()}
├─ Query: "{query}"
└─ Provider Selected: {provider_descriptions.get(provider, provider)}

Why {provider.upper()}?
"""
        
        # Add specific reasoning
        if task_type == TaskType.CODE:
            reason += "  • Expert at code generation and syntax\n"
            reason += "  • Understands programming paradigms\n"
            reason += "  • Produces production-ready code"
        elif task_type == TaskType.RESEARCH:
            reason += "  • Real-time web search capability\n"
            reason += "  • Returns latest information\n"
            reason += "  • Multi-source knowledge"
        elif task_type == TaskType.MATH:
            reason += "  • Strong mathematical reasoning\n"
            reason += "  • Step-by-step problem solving\n"
            reason += "  • Handles complex equations"
        elif task_type == TaskType.CREATIVE:
            reason += "  • Excellent creative writing\n"
            reason += "  • Unique imagination capabilities\n"
            reason += "  • Natural language fluency"
        elif task_type == TaskType.SYSTEM:
            reason += "  • Safety-conscious execution\n"
            reason += "  • Understands system implications\n"
            reason += "  • Prevents dangerous operations"
        else:
            reason += f"  • Best all-rounder for {task_type.value}"
        
        return reason

    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """
        Get information about a provider
        
        Args:
            provider: Provider name
        
        Returns:
            Provider information dictionary
        """
        provider_info = {
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
                "strengths": ["code", "creative", "complex reasoning"],
                "description": "Advanced language models with excellent code generation"
            },
            "deepseek": {
                "name": "DeepSeek",
                "models": ["deepseek-chat"],
                "strengths": ["math", "logic", "system commands"],
                "description": "Strong reasoning and mathematical problem-solving"
            },
            "gemini": {
                "name": "Google Gemini",
                "models": ["gemini-pro"],
                "strengths": ["research", "factual", "web search"],
                "description": "Excellent all-rounder with real-time web search"
            },
            "custom": {
                "name": "Custom Endpoint",
                "models": ["custom"],
                "strengths": ["local", "private", "custom"],
                "description": "User-provided AI endpoint"
            }
        }
        
        return provider_info.get(provider, {})

    def suggest_provider_override(self, default_provider: str, task_type: TaskType) -> Optional[str]:
        """
        Suggest provider override based on task type
        
        Args:
            default_provider: Currently set default provider
            task_type: Detected task type
        
        Returns:
            Suggested provider override or None
        """
        suggested = self.provider_mapping.get(task_type.value)
        
        if suggested and suggested != default_provider:
            logger.info(f"Suggesting provider override: {suggested} for {task_type.value}")
            return suggested
        
        return None


class ProviderFallback:
    """
    Handles fallback when primary provider is unavailable
    """

    def __init__(self):
        """Initialize fallback chains"""
        self.fallback_chains = {
            "openai": ["deepseek", "gemini", "custom"],
            "deepseek": ["openai", "gemini", "custom"],
            "gemini": ["openai", "deepseek", "custom"],
            "custom": ["openai", "deepseek", "gemini"]
        }

    def get_fallback_provider(self, primary_provider: str) -> str:
        """
        Get first fallback provider
        
        Args:
            primary_provider: Primary provider name
        
        Returns:
            Fallback provider name
        """
        chain = self.fallback_chains.get(primary_provider, ["gemini"])
        fallback = chain[0] if chain else "gemini"
        
        logger.warning(f"Primary provider {primary_provider} unavailable, using fallback: {fallback}")
        return fallback

    def get_full_fallback_chain(self, primary_provider: str) -> list:
        """
        Get full fallback chain
        
        Args:
            primary_provider: Primary provider name
        
        Returns:
            List of providers in fallback order
        """
        return [primary_provider] + self.fallback_chains.get(primary_provider, ["gemini"])


def main():
    """Test smart router"""
    config = {
        "ai": {
            "smart_routing": True,
            "default_provider": "gemini"
        }
    }
    
    router = SmartRouter(config)
    
    test_queries = [
        "Research blockchain technology",
        "Write a Python function for sorting",
        "Solve this integral: ∫x²dx",
        "Write me a funny poem about coding",
        "What's the capital of France?",
        "How do I secure my SSH server?"
    ]
    
    for query in test_queries:
        provider, task_type = router.route_query(query)
        print(f"\nQuery: {query}")
        print(f"Provider: {provider}")
        print(f"Task: {task_type.value}")


if __name__ == "__main__":
    main()
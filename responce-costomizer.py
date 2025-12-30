"""
Response Customization Module - Allows users to customize response types
Supports: detailed, concise, technical, simple, code-focused, bullet-point
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from jarvis.logger import get_logger
from jarvis.utils import load_config

logger = get_logger(__name__)


class ResponseType(Enum):
    """Available response types"""
    DETAILED = "detailed"
    CONCISE = "concise"
    TECHNICAL = "technical"
    SIMPLE = "simple"
    CODE = "code"
    BULLET = "bullet"


class ResponseFormat(Enum):
    """Response format options"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"


@dataclass
class ResponseProfile:
    """User's response customization profile"""
    response_type: ResponseType
    response_format: ResponseFormat
    include_examples: bool
    include_code: bool
    response_length: str  # short, medium, long
    language_level: str  # beginner, intermediate, advanced


class ResponseCustomizer:
    """
    Manages user response preferences and formatting
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize response customizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.customization_enabled = self.config.get('features', {}).get('response_customization', True)
        
        # Load user's response profile
        response_config = self.config.get('response_customization', {})
        
        self.profile = ResponseProfile(
            response_type=ResponseType(response_config.get('type', 'detailed')),
            response_format=ResponseFormat(response_config.get('format', 'text')),
            include_examples=response_config.get('include_examples', True),
            include_code=response_config.get('include_code', True),
            response_length=response_config.get('length', 'medium'),
            language_level=response_config.get('language_level', 'intermediate')
        )
        
        logger.info(f"Response customizer initialized with profile: {self.profile.response_type.value}")

    def customize_response(self, response: str, task_type: Optional[str] = None) -> str:
        """
        Apply customization to response
        
        Args:
            response: Original response text
            task_type: Optional task type for context
        
        Returns:
            Customized response
        """
        if not self.customization_enabled:
            return response
        
        # Apply response type formatting
        if self.profile.response_type == ResponseType.DETAILED:
            return self._format_detailed(response)
        elif self.profile.response_type == ResponseType.CONCISE:
            return self._format_concise(response)
        elif self.profile.response_type == ResponseType.TECHNICAL:
            return self._format_technical(response)
        elif self.profile.response_type == ResponseType.SIMPLE:
            return self._format_simple(response)
        elif self.profile.response_type == ResponseType.CODE:
            return self._format_code_focused(response)
        elif self.profile.response_type == ResponseType.BULLET:
            return self._format_bullet_point(response)
        
        return response

    def _format_detailed(self, response: str) -> str:
        """
        Format as detailed response with full explanations
        
        Args:
            response: Original response
        
        Returns:
            Detailed formatted response
        """
        # Add context and examples
        enhanced = response
        
        if self.include_examples and "example" not in response.lower():
            enhanced += "\n\n📝 Example:\n[Additional detailed example would be provided here]"
        
        if self.profile.language_level == "beginner":
            enhanced += "\n\n💡 Note: This explanation uses clear, simple language suitable for beginners."
        
        return enhanced

    def _format_concise(self, response: str) -> str:
        """
        Format as concise response with key points only
        
        Args:
            response: Original response
        
        Returns:
            Concise formatted response
        """
        # Keep only first 2-3 sentences/paragraphs
        lines = response.split('\n')
        concise_lines = []
        sentence_count = 0
        
        for line in lines:
            if not line.strip():
                continue
            
            concise_lines.append(line)
            sentence_count += line.count('.') + line.count('!') + line.count('?')
            
            if sentence_count >= 3:
                break
        
        return '\n'.join(concise_lines)

    def _format_technical(self, response: str) -> str:
        """
        Format as technical response with deep details
        
        Args:
            response: Original response
        
        Returns:
            Technical formatted response
        """
        # Add technical terminology and specifications
        technical = response
        
        # Add technical details if not present
        if "implementation" not in technical.lower():
            technical += "\n\n🔧 Implementation Details:\n[Technical specifications would be included]"
        
        if "performance" not in technical.lower():
            technical += "\n\n⚡ Performance Considerations:\n[Performance metrics would be included]"
        
        if "specifications" not in technical.lower():
            technical += "\n\n📋 Specifications:\n[Technical specs would be included]"
        
        return technical

    def _format_simple(self, response: str) -> str:
        """
        Format as simple/ELI5 response
        
        Args:
            response: Original response
        
        Returns:
            Simple formatted response
        """
        # Simplify language
        simple = response
        
        # Remove complex terminology and replace with simple explanations
        replacements = {
            'algorithm': 'step-by-step process',
            'framework': 'tool or structure',
            'paradigm': 'way of thinking',
            'architecture': 'structure or design',
            'implementation': 'putting it into practice',
            'optimization': 'making it faster/better',
            'protocol': 'set of rules',
            'interface': 'way to interact with something',
            'parameter': 'input or setting'
        }
        
        for complex_term, simple_term in replacements.items():
            simple = simple.replace(complex_term, f"{simple_term}")
        
        # Add ELI5 wrapper
        simple = f"🧒 Simple Explanation:\n\n{simple}"
        
        return simple

    def _format_code_focused(self, response: str) -> str:
        """
        Format as code-focused response with code examples
        
        Args:
            response: Original response
        
        Returns:
            Code-focused formatted response
        """
        code_response = response
        
        if self.include_code and "```" not in response:
            code_response += """\n\n💻 Code Example:
```python
# Example code would be provided here
# with practical implementation
```
"""
        
        return code_response

    def _format_bullet_point(self, response: str) -> str:
        """
        Format as bullet-point response
        
        Args:
            response: Original response
        
        Returns:
            Bullet-point formatted response
        """
        # Convert paragraphs to bullet points
        lines = response.split('\n')
        bullet_points = []
        
        for line in lines:
            if line.strip() and not line.startswith('•'):
                # Check if line looks like a key point
                if len(line) > 10:
                    bullet_points.append(f"• {line.strip()}")
            elif line.startswith('•'):
                bullet_points.append(line)
        
        result = '\n'.join(bullet_points)
        
        if not result:
            result = response
        
        return result

    def get_system_prompt_addition(self) -> str:
        """
        Get system prompt addition based on response customization
        
        Args:
        
        Returns:
            System prompt addition
        """
        prompt_parts = []
        
        # Add response type instruction
        if self.profile.response_type == ResponseType.DETAILED:
            prompt_parts.append("Provide detailed, comprehensive explanations with context and background.")
        elif self.profile.response_type == ResponseType.CONCISE:
            prompt_parts.append("Keep responses brief and to the point. Use only 2-3 key sentences.")
        elif self.profile.response_type == ResponseType.TECHNICAL:
            prompt_parts.append("Use technical terminology and provide deep technical details, specifications, and implementation notes.")
        elif self.profile.response_type == ResponseType.SIMPLE:
            prompt_parts.append("Explain everything in very simple terms, as if talking to a beginner or child. Avoid jargon.")
        elif self.profile.response_type == ResponseType.CODE:
            prompt_parts.append("Include practical, working code examples. Prioritize code samples and implementations.")
        elif self.profile.response_type == ResponseType.BULLET:
            prompt_parts.append("Format response as bullet points with key takeaways.")
        
        # Add language level
        if self.profile.language_level == "beginner":
            prompt_parts.append("Use simple, clear language suitable for beginners.")
        elif self.profile.language_level == "advanced":
            prompt_parts.append("Use advanced terminology and assume deep technical knowledge.")
        
        # Add examples instruction
        if self.profile.include_examples:
            prompt_parts.append("Include relevant examples where appropriate.")
        
        # Add code instruction
        if self.profile.include_code:
            prompt_parts.append("Include code examples when relevant to the topic.")
        
        return " ".join(prompt_parts)

    def update_profile(self, **kwargs) -> bool:
        """
        Update response profile
        
        Args:
            **kwargs: Fields to update (response_type, response_format, etc.)
        
        Returns:
            Success boolean
        """
        try:
            if 'response_type' in kwargs:
                self.profile.response_type = ResponseType(kwargs['response_type'])
            
            if 'response_format' in kwargs:
                self.profile.response_format = ResponseFormat(kwargs['response_format'])
            
            if 'include_examples' in kwargs:
                self.profile.include_examples = kwargs['include_examples']
            
            if 'include_code' in kwargs:
                self.profile.include_code = kwargs['include_code']
            
            if 'response_length' in kwargs:
                self.profile.response_length = kwargs['response_length']
            
            if 'language_level' in kwargs:
                self.profile.language_level = kwargs['language_level']
            
            logger.info(f"Response profile updated: {self.profile}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update response profile: {e}")
            return False

    def get_profile_info(self) -> Dict[str, Any]:
        """
        Get current profile information
        
        Returns:
            Profile information dictionary
        """
        return {
            'response_type': self.profile.response_type.value,
            'response_format': self.profile.response_format.value,
            'include_examples': self.profile.include_examples,
            'include_code': self.profile.include_code,
            'response_length': self.profile.response_length,
            'language_level': self.profile.language_level
        }

    def list_response_types(self) -> Dict[str, str]:
        """
        List available response types with descriptions
        
        Returns:
            Dictionary of response types and descriptions
        """
        return {
            'detailed': 'Full explanations with context (default)',
            'concise': 'Short, to-the-point answers',
            'technical': 'Deep technical details and specifications',
            'simple': 'Easy explanations for beginners (ELI5)',
            'code': 'Code examples and implementations',
            'bullet': 'Key points in bullet format'
        }


def main():
    """Test response customizer"""
    config = {
        'features': {'response_customization': True},
        'response_customization': {
            'type': 'detailed',
            'format': 'text',
            'include_examples': True,
            'include_code': True,
            'length': 'medium',
            'language_level': 'intermediate'
        }
    }
    
    customizer = ResponseCustomizer(config)
    
    # Test different response types
    test_response = "Python is a programming language."
    
    print("Available response types:")
    for rtype, desc in customizer.list_response_types().items():
        print(f"  • {rtype}: {desc}")
    
    # Test customization
    customizer.update_profile(response_type='simple')
    result = customizer.customize_response(test_response)
    print(f"\nSimple response:\n{result}")


if __name__ == "__main__":
    main()
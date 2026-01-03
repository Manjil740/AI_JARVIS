"""
COMPLETE CODE - direct_prompt_system.py
This is the FULL updated file with response customization features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Dict, Any, Optional
from datetime import datetime
import json

from jarvis.logger import get_logger
from jarvis.utils import load_config
from jarvis.ai_backend import AIBackend

# ✅ NEW IMPORT: Response customization
from response_customizer import ResponseCustomizer

logger = get_logger(__name__)


class DirectPromptSystem:
    """
    Direct prompt system with response customization
    Processes text prompts with customizable response types
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize prompt system with response customization
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        
        # ✅ NEW: Response customizer
        self.customizer = ResponseCustomizer(self.config)
        
        # Existing components
        self.ai_backend = AIBackend(self.config)
        
        # Prompt history
        self.prompt_history = []
        self.max_history = 50
        
        self.logger.info("Direct prompt system initialized")
        self.logger.info("Response customization: ENABLED")

    def process_prompt(self, prompt: str) -> str:
        """
        Process direct text prompt with customization support
        
        Args:
            prompt: Text prompt from user
        
        Returns:
            Customized response string
        """
        try:
            self.logger.info(f"Processing prompt: {prompt[:50]}...")
            
            # ✅ NEW: Check for customization commands first
            customization_response = self._handle_customization_command(prompt)
            if customization_response:
                self._add_to_history(prompt, customization_response, "customization")
                return customization_response
            
            # Check for preference commands
            if "show preferences" in prompt.lower() or "show settings" in prompt.lower():
                profile = self.customizer.get_profile_info()
                response = self._format_preferences(profile)
                self._add_to_history(prompt, response, "preference")
                return response
            
            # Check for help command
            if "help" in prompt.lower():
                response = self.show_help()
                self._add_to_history(prompt, response, "help")
                return response
            
            # Process as normal query
            response = self.ai_backend.query_sync(prompt)
            
            # ✅ NEW: Apply customization to response
            customized = self.customizer.customize_response(response)
            
            self._add_to_history(prompt, customized, "ai_query")
            
            return customized
            
        except Exception as e:
            self.logger.error(f"Prompt processing error: {e}", exc_info=True)
            error_msg = f"Error: {str(e)}"
            self._add_to_history(prompt, error_msg, "error")
            return error_msg

    def _handle_customization_command(self, prompt: str) -> Optional[str]:
        """
        Handle customization commands
        Returns response if customization command, None otherwise
        
        Args:
            prompt: Prompt string
        
        Returns:
            Response string or None
        """
        prompt_lower = prompt.lower()
        
        # ✅ CUSTOMIZE: Response type
        if prompt_lower.startswith("customize:") or prompt_lower.startswith("customize "):
            setting = prompt.replace("customize:", "").replace("customize ", "").strip()
            return self._apply_customization(setting)
        
        # ✅ RESET: To defaults
        if "reset preferences" in prompt_lower or "reset settings" in prompt_lower:
            self.customizer.update_profile(
                response_type='detailed',
                include_examples=True,
                include_code=True,
                language_level='intermediate'
            )
            return "✓ All settings reset to defaults"
        
        # Not a customization command
        return None

    def _apply_customization(self, setting: str) -> str:
        """
        Apply customization setting
        
        Args:
            setting: Setting to apply
        
        Returns:
            Response string
        """
        customizations = {
            # Response types
            "detailed": {"response_type": "detailed"},
            "detailed responses": {"response_type": "detailed"},
            "full": {"response_type": "detailed"},
            
            "concise": {"response_type": "concise"},
            "concise responses": {"response_type": "concise"},
            "short": {"response_type": "concise"},
            "brief": {"response_type": "concise"},
            
            "technical": {"response_type": "technical"},
            "technical responses": {"response_type": "technical"},
            "technical detail": {"response_type": "technical"},
            
            "simple": {"response_type": "simple"},
            "simple responses": {"response_type": "simple"},
            "easy": {"response_type": "simple"},
            "eli5": {"response_type": "simple"},
            
            "code": {"response_type": "code"},
            "code responses": {"response_type": "code"},
            "code examples": {"response_type": "code"},
            "code focused": {"response_type": "code"},
            
            "bullet": {"response_type": "bullet"},
            "bullet responses": {"response_type": "bullet"},
            "bullet points": {"response_type": "bullet"},
            "bullets": {"response_type": "bullet"},
            
            # Language levels
            "beginner": {"language_level": "beginner"},
            "beginner level": {"language_level": "beginner"},
            
            "intermediate": {"language_level": "intermediate"},
            "intermediate level": {"language_level": "intermediate"},
            
            "advanced": {"language_level": "advanced"},
            "advanced level": {"language_level": "advanced"},
            "expert": {"language_level": "advanced"},
            
            # Examples
            "with examples": {"include_examples": True},
            "include examples": {"include_examples": True},
            "show examples": {"include_examples": True},
            
            "without examples": {"include_examples": False},
            "no examples": {"include_examples": False},
            "exclude examples": {"include_examples": False},
            
            # Code
            "with code": {"include_code": True},
            "include code": {"include_code": True},
            "show code": {"include_code": True},
            
            "without code": {"include_code": False},
            "no code": {"include_code": False},
            "exclude code": {"include_code": False},
            
            # Response length
            "short": {"response_length": "short"},
            "medium": {"response_length": "medium"},
            "long": {"response_length": "long"},
        }
        
        # Try to find matching customization
        setting_lower = setting.lower()
        for key, value in customizations.items():
            if key in setting_lower:
                success = self.customizer.update_profile(**value)
                if success:
                    type_name = list(value.keys())[0]
                    type_value = list(value.values())[0]
                    return f"✓ Setting updated: {type_name} = {type_value}"
        
        # Not recognized
        suggestions = """❌ Customization not recognized: '{}'

Try one of these:

Response Types:
  • customize detailed      → Full explanations
  • customize concise       → Short answers
  • customize technical     → Deep technical
  • customize simple        → Beginner friendly (ELI5)
  • customize code          → Code examples
  • customize bullet        → Bullet points

Language Levels:
  • customize beginner      → Easy language
  • customize intermediate  → Normal language
  • customize advanced      → Complex language

Examples & Code:
  • customize with examples → Include examples
  • customize without examples → No examples
  • customize with code     → Include code snippets
  • customize without code  → No code snippets

Other:
  • show preferences        → View current settings
  • reset preferences       → Back to defaults
""".format(setting)
        
        return suggestions

    def _format_preferences(self, profile: Dict) -> str:
        """
        Format preferences for display
        
        Args:
            profile: Profile dictionary
        
        Returns:
            Formatted preferences string
        """
        output = "📋 Current Preferences:\n"
        output += "=" * 40 + "\n"
        output += f"Response Type: {profile.get('response_type', 'detailed').upper()}\n"
        output += f"Language Level: {profile.get('language_level', 'intermediate').title()}\n"
        output += f"Include Examples: {'Yes' if profile.get('include_examples') else 'No'}\n"
        output += f"Include Code: {'Yes' if profile.get('include_code') else 'No'}\n"
        output += f"Response Length: {profile.get('response_length', 'medium').title()}\n"
        output += "=" * 40 + "\n"
        output += "\nTip: Use 'customize [type]' to change settings\n"
        output += "Example: 'customize simple' or 'customize technical'\n"
        
        return output

    def show_help(self) -> str:
        """
        Show help message
        
        Returns:
            Help text
        """
        help_text = """
🤖 JARVIS Direct Prompt System - Help

📝 BASIC USAGE:
  • Type any question or command
  • Responses are customized based on your preferences
  • All responses are logged for history

✨ CUSTOMIZATION COMMANDS:
  Response Types:
    customize detailed      → Full explanations with examples
    customize concise       → Short, direct answers
    customize technical     → Deep technical details
    customize simple        → Beginner-friendly (ELI5)
    customize code          → Code examples focused
    customize bullet        → Bullet point format

  Language Levels:
    customize beginner      → Simple, easy language
    customize intermediate  → Normal language
    customize advanced      → Complex, technical language

  Options:
    customize with examples → Include examples in responses
    customize without examples → Skip examples
    customize with code     → Include code snippets
    customize without code  → No code examples
    customize short         → Brief responses
    customize medium        → Medium length
    customize long          → Detailed responses

📋 PREFERENCE COMMANDS:
  show preferences        → View all current settings
  reset preferences       → Reset to defaults

💡 EXAMPLES:
  Q: customize simple
  A: ✓ Setting updated: response_type = simple
  
  Q: What is Python?
  A: Python is a programming language that's easy to learn...
  
  Q: customize technical
  Q: What is Python?
  A: Python is a dynamically-typed, interpreted language...

🎯 SMART FEATURES:
  • Automatic provider selection based on task type
  • Customizable response formats
  • Response history tracking
  • Settings persistence

📞 MORE INFO:
  • Use 'help' to see this message again
  • Preferences are saved between sessions
  • All customizations are reversible

"""
        return help_text

    def _add_to_history(self, prompt: str, response: str, source: str) -> None:
        """
        Add prompt and response to history
        
        Args:
            prompt: Prompt string
            response: Response string
            source: Source type (ai_query, customization, preference, etc.)
        """
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'response': response[:500],  # Store first 500 chars
                'source': source,
            }
            
            self.prompt_history.append(entry)
            
            # Keep only last N items
            if len(self.prompt_history) > self.max_history:
                self.prompt_history = self.prompt_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"History error: {e}")

    def get_history(self, limit: int = 10) -> list:
        """
        Get prompt history
        
        Args:
            limit: Number of entries to return
        
        Returns:
            List of history entries
        """
        return self.prompt_history[-limit:] if self.prompt_history else []

    def clear_history(self) -> None:
        """Clear prompt history"""
        self.prompt_history = []
        self.logger.info("Prompt history cleared")

    def export_preferences(self) -> Dict[str, Any]:
        """
        Export current preferences
        
        Returns:
            Preferences dictionary
        """
        return self.customizer.get_profile_info()

    def import_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Import preferences from dictionary
        
        Args:
            preferences: Preferences dictionary
        
        Returns:
            Boolean indicating success
        """
        try:
            return self.customizer.update_profile(**preferences)
        except Exception as e:
            self.logger.error(f"Import preferences error: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get system status
        
        Returns:
            Status dictionary
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'ai_backend': self.ai_backend.get_status(),
            'response_customization_enabled': True,
            'current_preferences': self.customizer.get_profile_info(),
            'prompt_history_count': len(self.prompt_history),
        }


def main():
    """Test direct prompt system"""
    config = load_config()
    dps = DirectPromptSystem(config)
    
    print("🎯 JARVIS Direct Prompt System")
    print("=" * 50)
    print("Commands to try:")
    print("  'customize simple' - Set to simple responses")
    print("  'what is AI?' - Get response in current style")
    print("  'customize technical' - Switch to technical")
    print("  'show preferences' - View settings")
    print("  'help' - Show help")
    print("  'exit' - Quit")
    print("=" * 50)
    
    while True:
        try:
            prompt = input("\n> ").strip()
            
            if prompt.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not prompt:
                continue
            
            response = dps.process_prompt(prompt)
            print(f"\n{response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
"""
COMPLETE CODE - voice_command_system.py
This is the FULL updated file with all new intelligent features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json

from jarvis.logger import get_logger
from jarvis.utils import load_config
from jarvis.voice_engine import VoiceEngine
from jarvis.ai_backend import AIBackend

# ✅ NEW IMPORTS: Intelligent features
from app_intelligence import AppIntelligenceEngine
from enhanced_security import EnhancedSecurityManager
from voice_biometric import DebugModeManager

logger = get_logger(__name__)


class VoiceCommandSystem:
    """
    Voice command system with intelligent features
    Processes voice commands with app intelligence, security, and biometrics
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize voice command system with all intelligent features
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        
        # ✅ NEW: Intelligent features
        self.app_engine = AppIntelligenceEngine(self.config)
        self.security = EnhancedSecurityManager(self.config)
        self.debug_manager = DebugModeManager(self.config)
        self.voice_biometric = self.debug_manager.voice_bio
        
        # Existing components
        self.voice_engine = VoiceEngine(self.config)
        self.ai_backend = AIBackend(self.config)
        
        # Command history
        self.command_history = []
        self.max_history = 100
        
        self.logger.info("Voice command system initialized")
        self.logger.info("App intelligence: ENABLED")
        self.logger.info("Enhanced security: ENABLED")
        self.logger.info("Voice biometric: ENABLED")

    def listen_and_process(self) -> str:
        """
        Listen for voice command and process it
        
        Returns:
            Response string
        """
        try:
            self.logger.info("Listening for voice command...")
            
            # Listen for voice
            command = self.voice_engine.listen(timeout=10)
            
            if not command:
                return "No command heard. Please try again."
            
            self.logger.info(f"Command heard: {command}")
            
            # Process the command
            response = self.process_command(command)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Listen and process error: {e}", exc_info=True)
            return f"Error processing voice command: {str(e)}"

    def _process_intelligent_command(self, command: str) -> Optional[str]:
        """
        Process command with intelligent features
        Returns None if not an intelligent command, otherwise returns response
        
        Args:
            command: Command string
        
        Returns:
            Response string or None if not intelligent command
        """
        command_lower = command.lower()
        
        # ✅ CHECK 1: Sudo keyword (for dangerous commands)
        is_sudo, duration, reason = self.security.parse_sudo_keyword(command)
        if is_sudo:
            success, msg = self.security.activate_sudo_mode(duration)
            self.logger.info(f"Sudo mode activated: {duration}s")
            return msg
        
        # ✅ CHECK 2: App intelligence ("I need/want...")
        app_triggers = ["i need", "i want", "find me", "install", "setup"]
        if any(trigger in command_lower for trigger in app_triggers):
            app_type = self._extract_app_type(command)
            if app_type:
                self.logger.info(f"App intelligence: searching for {app_type}")
                success, formatted, recommendation = self.app_engine.full_workflow(app_type)
                if success:
                    prompt = "\n\nWould you like me to install it? Say 'Yes' or 'No'"
                    return formatted + prompt
        
        # ✅ CHECK 3: Debug mode access
        if "debug mode" in command_lower or "debugmode" in command_lower.replace(" ", ""):
            # Extract keyword from command
            keyword = command.lower()
            success, msg = self.debug_manager.authenticate(method="keyword", keyword=keyword)
            if success:
                self.logger.info("Debug mode access granted")
                return "✓ Debug mode access granted. Opening control portal..."
            else:
                self.logger.warning("Debug mode access denied")
                return "✗ Debug mode access denied. Invalid keyword. Use 'debugmode code 0'"
        
        # ✅ CHECK 4: Voice biometric enrollment
        if "enroll voice" in command_lower or "voice profile" in command_lower:
            self.logger.info("Voice enrollment requested")
            success, msg = self.voice_biometric.enroll_voice_profile()
            return msg
        
        # ✅ CHECK 5: Voice verification
        if "verify voice" in command_lower or "voice verify" in command_lower:
            self.logger.info("Voice verification requested")
            success, msg = self.voice_biometric.verify_voice()
            return msg
        
        # ✅ CHECK 6: System status
        if "system status" in command_lower or "show status" in command_lower:
            status = self.get_system_status()
            return self._format_status(status)
        
        # Not an intelligent command
        return None

    def _extract_app_type(self, command: str) -> Optional[str]:
        """
        Extract application type from command
        
        Args:
            command: Command string
        
        Returns:
            App type string or None
        """
        phrases = ["i need a", "i want a", "i need", "i want", "find me a", "install"]
        
        command_lower = command.lower()
        for phrase in phrases:
            if phrase in command_lower:
                parts = command_lower.split(phrase)
                if len(parts) > 1:
                    app_type = parts[1].strip().rstrip('?.,!;')
                    # Clean up the app type
                    return app_type[:50]  # Limit to 50 chars
        
        return None

    def process_command(self, command: str) -> str:
        """
        Main command processor with intelligent features
        
        Args:
            command: Command string from user
        
        Returns:
            Response string
        """
        try:
            self.logger.info(f"Processing command: {command[:50]}...")
            
            # ✅ NEW: Try intelligent features first
            intelligent_response = self._process_intelligent_command(command)
            if intelligent_response:
                self._add_to_history(command, intelligent_response, "intelligent")
                return intelligent_response
            
            # Fall back to normal AI query
            response = self.ai_backend.query_sync(command)
            self._add_to_history(command, response, "ai_query")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Command processing error: {e}", exc_info=True)
            error_msg = f"Error processing command: {str(e)}"
            self._add_to_history(command, error_msg, "error")
            return error_msg

    def _add_to_history(self, command: str, response: str, source: str) -> None:
        """
        Add command and response to history
        
        Args:
            command: Command string
            response: Response string
            source: Source (intelligent, ai_query, error)
        """
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'command': command,
                'response': response[:500],  # Store first 500 chars
                'source': source,
            }
            
            self.command_history.append(entry)
            
            # Keep only last N items
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"History error: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get complete system status including all intelligent features
        
        Returns:
            Status dictionary
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'voice_engine': {
                'status': 'online',
                'listening': False,
            },
            'ai_backend': self.ai_backend.get_status(),
            'app_intelligence': {
                'enabled': True,
                'status': 'operational',
            },
            'enhanced_security': {
                'enabled': True,
                'sudo_active': self.security.is_sudo_active(),
                'sudo_remaining': self.security.get_sudo_remaining_time(),
            },
            'voice_biometric': self.voice_biometric.get_security_status(),
            'command_history_count': len(self.command_history),
        }

    def _format_status(self, status: Dict[str, Any]) -> str:
        """
        Format status for display
        
        Args:
            status: Status dictionary
        
        Returns:
            Formatted status string
        """
        output = "🤖 JARVIS System Status\n"
        output += "=" * 40 + "\n"
        output += f"AI Provider: {status['ai_backend']['current_provider']}\n"
        output += f"Smart Routing: {'Enabled' if status['ai_backend']['smart_routing_enabled'] else 'Disabled'}\n"
        output += f"App Intelligence: {'Enabled' if status['app_intelligence']['enabled'] else 'Disabled'}\n"
        output += f"Enhanced Security: {'Enabled' if status['enhanced_security']['enabled'] else 'Disabled'}\n"
        
        if status['enhanced_security']['sudo_active']:
            remaining = status['enhanced_security']['sudo_remaining']
            output += f"Sudo Mode: Active ({remaining}s remaining)\n"
        else:
            output += "Sudo Mode: Inactive\n"
        
        output += f"Commands Processed: {status['command_history_count']}\n"
        output += "=" * 40 + "\n"
        
        return output

    def get_history(self, limit: int = 10) -> list:
        """
        Get command history
        
        Args:
            limit: Number of entries to return
        
        Returns:
            List of history entries
        """
        return self.command_history[-limit:] if self.command_history else []

    def clear_history(self) -> None:
        """Clear command history"""
        self.command_history = []
        self.logger.info("Command history cleared")

    def speak(self, text: str) -> bool:
        """
        Speak response using text-to-speech
        
        Args:
            text: Text to speak
        
        Returns:
            Boolean indicating success
        """
        try:
            return self.voice_engine.speak(text)
        except Exception as e:
            self.logger.error(f"Speech error: {e}")
            return False

    def is_sudo_active(self) -> bool:
        """
        Check if sudo mode is currently active
        
        Returns:
            Boolean indicating sudo mode status
        """
        return self.security.is_sudo_active()

    def get_sudo_remaining(self) -> int:
        """
        Get remaining sudo mode time
        
        Returns:
            Remaining seconds
        """
        return self.security.get_sudo_remaining_time()


def main():
    """Test voice command system"""
    config = load_config()
    vcs = VoiceCommandSystem(config)
    
    print("🎤 JARVIS Voice Command System")
    print("=" * 40)
    print("Commands to try:")
    print("  'i need a pdf reader' - App intelligence")
    print("  'research python' - Smart routing")
    print("  'sudo code 0' - Enhanced security")
    print("  'enroll voice' - Voice biometric")
    print("  'system status' - Get status")
    print("  'exit' - Quit")
    print("=" * 40)
    
    while True:
        try:
            print("\n🎤 Listening...")
            command = input("Or type command: ").strip()
            
            if command.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not command:
                continue
            
            response = vcs.process_command(command)
            print(f"\n🤖 {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
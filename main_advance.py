"""
JARVIS Main Advanced - Primary entry point for the voice AI assistant
Runs as a headless systemd service with voice I/O and subtitles
"""

import sys
import os
import signal
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from jarvis.logger import get_logger
from jarvis.utils import load_config, validate_api_key
from jarvis.voice_engine import VoiceController
from jarvis.ai_backend import AIBackend
from jarvis.command_executor import CommandExecutor
from jarvis.subtitle_overlay import SubtitleManager
from jarvis.security import SudoSession

logger = get_logger(__name__)


class JARVISAssistant:
    """
    Main JARVIS Voice AI Assistant
    Runs as headless service with voice I/O and optional subtitles
    """

    def __init__(self):
        """Initialize JARVIS assistant"""
        self.running = False
        self.config = None
        self.voice_controller = None
        self.ai_backend = None
        self.command_executor = None
        self.subtitle_manager = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle termination signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("JARVIS Voice AI Assistant - Initializing")
            logger.info("=" * 60)

            # Load configuration
            logger.info("Loading configuration...")
            self.config = load_config()
            logger.info("Configuration loaded successfully")

            # Validate API keys
            logger.info("Checking API keys...")
            if not self._check_api_keys():
                logger.error("No valid API keys found!")
                return False

            # Initialize voice controller
            logger.info("Initializing voice engine...")
            self.voice_controller = VoiceController(self.config)
            logger.info(f"Wake word: '{self.config['audio']['wake_word']}'")

            # Initialize AI backend
            logger.info("Initializing AI backend...")
            self.ai_backend = AIBackend(self.config)
            if not self.ai_backend.is_ready():
                logger.error("AI backend initialization failed!")
                return False

            # Initialize command executor
            logger.info("Initializing command executor...")
            self.command_executor = CommandExecutor(self.config)

            # Initialize subtitle manager
            logger.info("Initializing subtitle system...")
            self.subtitle_manager = SubtitleManager(self.config)
            if self.config.get('ui', {}).get('subtitles_enabled', True):
                self.subtitle_manager.start()

            logger.info("=" * 60)
            logger.info("JARVIS initialized successfully!")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def _check_api_keys(self) -> bool:
        """
        Check if at least one API key is configured
        
        Returns:
            True if at least one key is available
        """
        providers = ['openai', 'deepseek', 'gemini', 'custom']
        for provider in providers:
            if validate_api_key(provider):
                logger.info(f"Found API key for: {provider}")
                return True
        
        logger.warning("No API keys found in environment variables:")
        logger.warning("  - OPENAI_API_KEY")
        logger.warning("  - DEEPSEEK_API_KEY")
        logger.warning("  - GEMINI_API_KEY")
        logger.warning("  - CUSTOM_AI_API_KEY")
        return False

    def run(self) -> None:
        """
        Main service loop - listen for wake word and process commands
        """
        self.running = True
        logger.info("Starting main service loop...")
        logger.info("Listening for wake word...")

        try:
            while self.running:
                try:
                    # Listen for wake word
                    if self.voice_controller.listen_for_wake_word():
                        logger.info("Wake word detected!")
                        self.subtitle_manager.show("Listening for command...")
                        
                        # Listen for command
                        command_text = self.voice_controller.listen_for_command()
                        if command_text:
                            logger.info(f"Command received: {command_text}")
                            self.subtitle_manager.show(f"Processing: {command_text}")
                            
                            # Check for sudo keyword
                            if self.command_executor.check_sudo_keyword(command_text):
                                self.voice_controller.speak("Sudo mode activated for 5 minutes")

                            # Process command
                            self._process_command(command_text)
                        else:
                            logger.warning("Command timeout or error")
                            self.voice_controller.speak("I didn't catch that, please try again")

                        # Small delay before listening again
                        time.sleep(1)

                except KeyboardInterrupt:
                    logger.info("Interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    time.sleep(2)  # Brief delay before retry

        finally:
            self.shutdown()

    def _process_command(self, command_text: str) -> None:
        """
        Process a voice command
        
        Args:
            command_text: User's command text
        """
        try:
            # First, try to parse as a direct command
            intent = self.command_executor.parse_intent(command_text)
            
            if intent:
                # Execute the parsed intent
                logger.info(f"Executing intent: {intent.intent_type} - {intent.action}")
                success, message = self.command_executor.execute(intent)
                
                self.voice_controller.speak(message)
                self.subtitle_manager.show(message)
            else:
                # Send to AI for processing
                logger.info("Sending command to AI backend...")
                response = self.ai_backend.query_sync(command_text)
                
                if response:
                    spoken_message = response.get('spoken_message', response.get('text', ''))
                    logger.info(f"AI Response: {spoken_message[:100]}")
                    
                    self.voice_controller.speak(spoken_message)
                    self.subtitle_manager.show(spoken_message)
                else:
                    logger.warning("AI backend returned no response")
                    self.voice_controller.speak("I'm having trouble processing that right now")
                    self.subtitle_manager.show("AI Error")

        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            error_message = "An error occurred while processing your command"
            self.voice_controller.speak(error_message)
            self.subtitle_manager.show(error_message)

    def shutdown(self) -> None:
        """Gracefully shutdown JARVIS"""
        logger.info("Shutting down JARVIS...")
        self.running = False

        try:
            if self.subtitle_manager:
                self.subtitle_manager.stop()
            logger.info("Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    try:
        logger.info("Starting JARVIS Voice AI Assistant")
        
        # Create assistant
        jarvis = JARVISAssistant()

        # Initialize components
        if not jarvis.initialize():
            logger.error("Failed to initialize JARVIS")
            sys.exit(1)

        # Run main loop
        jarvis.run()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
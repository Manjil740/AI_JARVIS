"""
JARVIS Main - Simple entry point for testing and development
Alternative to main_advanced.py with simpler functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis.logger import get_logger
from jarvis.utils import load_config
from jarvis.voice_engine import VoiceController
from jarvis.ai_backend import AIBackend
from jarvis.command_executor import CommandExecutor

logger = get_logger(__name__)


def simple_interactive_mode():
    """Simple interactive testing mode"""
    logger.info("JARVIS - Simple Interactive Mode")
    print("\n" + "="*50)
    print("JARVIS Voice AI Assistant - Simple Mode")
    print("="*50)

    try:
        # Load config
        config = load_config()
        
        # Initialize components
        voice = VoiceController(config)
        ai = AIBackend(config)
        executor = CommandExecutor(config)

        if not ai.is_ready():
            print("❌ No AI provider configured!")
            print("Please set OPENAI_API_KEY or another provider key")
            return

        print("✅ JARVIS initialized")
        print("\nListening for wake word: 'hello jarvis'")
        print("Say 'quit' to exit\n")

        while True:
            # Listen for wake word
            if voice.listen_for_wake_word():
                print("\n🎤 Wake word detected!")
                voice.speak("I'm listening")
                
                # Get command
                command = voice.listen_for_command()
                if command:
                    if command.lower() in ['quit', 'exit', 'bye']:
                        voice.speak("Goodbye!")
                        break

                    print(f"📝 Command: {command}")

                    # Try to parse as direct command
                    intent = executor.parse_intent(command)
                    
                    if intent:
                        success, msg = executor.execute(intent)
                        voice.speak(msg)
                        print(f"✅ {msg}")
                    else:
                        # Send to AI
                        print("🤖 Querying AI...")
                        response = ai.query_sync(command)
                        
                        if response:
                            message = response.get('spoken_message', response.get('text', ''))
                            voice.speak(message)
                            print(f"🤖 {message}")
                        else:
                            voice.speak("I'm having trouble responding")
                            print("❌ AI response failed")

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")


def cli_mode():
    """Command-line interface mode (no voice)"""
    logger.info("JARVIS - CLI Mode")
    print("\n" + "="*50)
    print("JARVIS - Command Line Interface")
    print("="*50)

    try:
        config = load_config()
        ai = AIBackend(config)

        if not ai.is_ready():
            print("❌ No AI provider configured!")
            return

        print("✅ Ready to process commands")
        print("Type 'help' for commands, 'exit' to quit\n")

        while True:
            try:
                user_input = input("JARVIS> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit']:
                    print("Goodbye!")
                    break

                if user_input.lower() == 'help':
                    print("""
                    Available commands:
                    ask <query>   - Query the AI
                    exit/quit     - Exit the program
                    Any other text is sent to AI
                    """)
                    continue

                print("🤖 Processing...")
                response = ai.query_sync(user_input)

                if response:
                    print(f"JARVIS: {response.get('text', 'No response')}\n")
                else:
                    print("❌ No response\n")

            except KeyboardInterrupt:
                print("\n\nShutting down...")
                break

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("""
        JARVIS Main - Choose mode:
        
        Usage: python3 main.py [mode]
        
        Modes:
          voice   - Voice-interactive mode (default)
          cli     - Command-line mode (text input)
          help    - Show this help
        """)
        mode = input("Select mode (voice/cli): ").lower().strip()

    if mode in ['help', '-h', '--help']:
        print("""
        JARVIS Voice AI Assistant - Main Interface
        
        Voice Mode: Interactive voice commands
          Usage: python3 main.py voice
          
        CLI Mode: Text-based interface
          Usage: python3 main.py cli
          
        Features:
          - Speech recognition & TTS
          - Multi-provider LLM
          - Command execution
          - File operations
          - GUI automation
        """)
    elif mode == 'cli':
        cli_mode()
    else:
        # Default to voice mode
        simple_interactive_mode()


if __name__ == "__main__":
    main()
"""
Command Executor Module - Executes voice commands and user actions
Integrates with security, file operations, downloads, and GUI automation
"""

import subprocess
import os
import json
import re
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from jarvis.logger import get_logger
from jarvis.security import SecurityChecker, SudoSession, DownloadValidator
from jarvis.screen_controller import ScreenController

logger = get_logger(__name__)


class CommandIntent:
    """Represents a parsed command intent"""

    def __init__(self, intent_type: str, action: str, params: Dict[str, Any] = None):
        """
        Initialize command intent
        
        Args:
            intent_type: Type of intent (shell, file, download, gui, app)
            action: Action to perform
            params: Parameters for the action
        """
        self.intent_type = intent_type
        self.action = action
        self.params = params or {}


class CommandExecutor:
    """
    Executes commands based on parsed intents
    Handles security checks, downloads, file operations, and GUI automation
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize command executor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.security_config = config.get('security', {})
        
        self.security_checker = SecurityChecker(
            self.security_config.get('dangerous_keywords', [])
        )
        self.sudo_session = SudoSession(
            self.security_config.get('sudo_mode_duration', 300)
        )
        self.download_validator = DownloadValidator()
        self.screen_controller = ScreenController()

    def parse_intent(self, command_text: str) -> Optional[CommandIntent]:
        """
        Parse command text into intent
        
        Args:
            command_text: User's spoken/typed command
        
        Returns:
            CommandIntent or None if unparseable
        """
        if not command_text or not isinstance(command_text, str):
            return None

        command_lower = command_text.lower().strip()

        # Shell command execution
        if command_lower.startswith(('run ', 'execute ', 'shell ')):
            action = command_text[len(command_lower.split()[0]) + 1:].strip()
            return CommandIntent('shell', action)

        # File operations
        if 'edit' in command_lower or 'open' in command_lower:
            if 'file' in command_lower:
                # Extract filename
                match = re.search(r'(edit|open)\s+(?:file\s+)?(["\']?)([^"\']+)\2', command_text, re.IGNORECASE)
                if match:
                    filename = match.group(3)
                    return CommandIntent('file', 'edit', {'filename': filename})

        # Download command
        if 'download' in command_lower:
            match = re.search(r'download\s+(?:from\s+)?([^\s]+)', command_text, re.IGNORECASE)
            if match:
                url = match.group(1)
                return CommandIntent('download', 'fetch', {'url': url})

        # App opening
        if 'open' in command_lower or 'launch' in command_lower or 'start' in command_lower:
            match = re.search(r'(?:open|launch|start)\s+(["\']?)([^"\']+)\1', command_text, re.IGNORECASE)
            if match:
                app_name = match.group(2)
                return CommandIntent('app', 'open', {'app': app_name})

        # GUI automation
        if 'click' in command_lower:
            match = re.search(r'click\s+(?:on\s+)?([^,]+)', command_text, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                return CommandIntent('gui', 'click', {'target': target})

        # Scroll command
        if 'scroll' in command_lower:
            direction = 'down' if 'down' in command_lower else 'up' if 'up' in command_lower else 'down'
            return CommandIntent('gui', 'scroll', {'direction': direction})

        # Type command
        if 'type' in command_lower:
            match = re.search(r'type\s+(["\']?)([^"\']+)\1', command_text, re.IGNORECASE)
            if match:
                text = match.group(2)
                return CommandIntent('gui', 'type', {'text': text})

        return None

    def execute(self, intent: CommandIntent) -> Tuple[bool, str]:
        """
        Execute command intent
        
        Args:
            intent: CommandIntent to execute
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not intent:
            return False, "No valid intent"

        try:
            if intent.intent_type == 'shell':
                return self._execute_shell(intent.action)
            elif intent.intent_type == 'file':
                return self._execute_file_operation(intent.action, intent.params)
            elif intent.intent_type == 'download':
                return self._execute_download(intent.params)
            elif intent.intent_type == 'app':
                return self._execute_app_open(intent.params)
            elif intent.intent_type == 'gui':
                return self._execute_gui_action(intent.action, intent.params)
            else:
                return False, f"Unknown intent type: {intent.intent_type}"

        except Exception as e:
            logger.error(f"Execution error: {e}")
            return False, f"Execution failed: {str(e)}"

    def _execute_shell(self, command: str) -> Tuple[bool, str]:
        """Execute shell command"""
        if not self.security_config.get('allow_system_commands', False):
            return False, "System commands are disabled"

        allowed, reason = self.security_checker.check_command(command, self.sudo_session.is_valid())
        if not allowed:
            return False, reason

        try:
            logger.info(f"Executing shell command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=self.security_config.get('command_timeout', 30),
                text=True,
            )

            if result.returncode == 0:
                return True, f"Command executed: {result.stdout[:100]}"
            else:
                return False, f"Command failed: {result.stderr[:100]}"

        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            logger.error(f"Shell execution error: {e}")
            return False, str(e)

    def _execute_file_operation(self, action: str, params: dict) -> Tuple[bool, str]:
        """Execute file operation"""
        if not self.config.get('features', {}).get('file_editing', False):
            return False, "File editing is disabled"

        filename = params.get('filename', '')
        if not filename:
            return False, "No filename specified"

        try:
            filepath = Path(filename).expanduser()
            
            if action == 'edit':
                logger.info(f"Opening file for editing: {filepath}")
                # Use default editor
                os.system(f"$EDITOR {filepath}")
                return True, f"Opened {filepath}"
            
            elif action == 'read':
                if filepath.exists():
                    with open(filepath, 'r') as f:
                        content = f.read()
                    return True, content[:500]
                else:
                    return False, f"File not found: {filepath}"

        except Exception as e:
            logger.error(f"File operation error: {e}")
            return False, str(e)

    def _execute_download(self, params: dict) -> Tuple[bool, str]:
        """Execute download operation"""
        if not self.config.get('features', {}).get('downloads', False):
            return False, "Downloads are disabled"

        url = params.get('url', '')
        if not url:
            return False, "No URL specified"

        valid, reason = self.download_validator.validate_url(url)
        if not valid:
            return False, reason

        try:
            logger.info(f"Downloading from: {url}")
            import urllib.request
            filename = url.split('/')[-1] or 'download'
            
            valid_fname, fname_reason = self.download_validator.validate_filename(filename)
            if not valid_fname:
                return False, fname_reason

            filepath = Path(f"./downloads/{filename}").expanduser()
            filepath.parent.mkdir(parents=True, exist_ok=True)

            urllib.request.urlretrieve(url, filepath)
            logger.info(f"Downloaded to: {filepath}")
            return True, f"Downloaded to {filepath}"

        except Exception as e:
            logger.error(f"Download error: {e}")
            return False, str(e)

    def _execute_app_open(self, params: dict) -> Tuple[bool, str]:
        """Execute app opening"""
        if not self.config.get('features', {}).get('gui_automation', False):
            return False, "GUI automation is disabled"

        app = params.get('app', '')
        if not app:
            return False, "No app specified"

        return self.screen_controller.open_app(app)

    def _execute_gui_action(self, action: str, params: dict) -> Tuple[bool, str]:
        """Execute GUI action"""
        if not self.config.get('features', {}).get('gui_automation', False):
            return False, "GUI automation is disabled"

        try:
            if action == 'click':
                target = params.get('target', '')
                logger.info(f"GUI: Click on {target}")
                # Simplified: would need image recognition or UI element mapping
                return True, f"Clicked on {target}"

            elif action == 'scroll':
                direction = params.get('direction', 'down')
                width, height = self.screen_controller.get_screen_size()
                center_x, center_y = width // 2, height // 2
                self.screen_controller.scroll(center_x, center_y, direction=direction)
                return True, f"Scrolled {direction}"

            elif action == 'type':
                text = params.get('text', '')
                self.screen_controller.type_text(text)
                return True, f"Typed: {text[:50]}"

            else:
                return False, f"Unknown GUI action: {action}"

        except Exception as e:
            logger.error(f"GUI action error: {e}")
            return False, str(e)

    def check_sudo_keyword(self, text: str) -> bool:
        """
        Check if sudo keyword is present and activate session if needed
        
        Args:
            text: Text to check
        
        Returns:
            True if sudo session is now active
        """
        sudo_keyword = self.config.get('sudo', {}).get('keyword', 'sudo code')
        
        if sudo_keyword.lower() in text.lower():
            logger.warning(f"Sudo keyword detected: {sudo_keyword}")
            return self.sudo_session.activate()
        
        return False
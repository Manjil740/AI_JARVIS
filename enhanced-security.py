"""
Enhanced Security Module - Custom sudo keywords and advanced privilege escalation
Default keyword: "sudo code 0"
Supports time-based access: "sudo code 300", "sudo code 1800", etc.
"""

import time
import subprocess
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from jarvis.logger import get_logger
from jarvis.utils import load_config

logger = get_logger(__name__)


class SudoSession:
    """Represents an active sudo session"""
    
    def __init__(self, duration_seconds: int = 300):
        """
        Initialize sudo session
        
        Args:
            duration_seconds: How long the session lasts
        """
        self.start_time = datetime.now()
        self.duration = timedelta(seconds=duration_seconds)
        self.end_time = self.start_time + self.duration
        self.is_active = True
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        if not self.is_active:
            return False
        
        if datetime.now() > self.end_time:
            self.is_active = False
            logger.warning("Sudo session expired")
            return False
        
        return True
    
    def get_remaining_time(self) -> int:
        """Get remaining session time in seconds"""
        if not self.is_valid():
            return 0
        
        remaining = (self.end_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def end_session(self):
        """Manually end the session"""
        self.is_active = False
        logger.info("Sudo session ended manually")


class EnhancedSecurityManager:
    """
    Manages sudo sessions with custom keywords and time-based access
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize security manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        security_config = self.config.get('security', {})
        
        # Custom sudo keyword (default: "sudo code 0")
        self.sudo_keyword = security_config.get('sudo_keyword', 'sudo code 0')
        self.default_sudo_duration = security_config.get('sudo_mode_duration', 300)
        self.allow_custom_sudo = security_config.get('allow_custom_sudo', True)
        self.allow_timed_sudo = security_config.get('allow_timed_sudo', True)
        
        # Current active session
        self.current_session: Optional[SudoSession] = None
        
        # Dangerous commands that require extra confirmation
        self.dangerous_commands = [
            'rm -rf',
            'dd if=',
            'mkfs',
            'fdisk',
            'shutdown',
            'reboot',
            'halt',
            'kill -9',
            'pkill -9',
            'chmod 777',
            'chown',
            'usermod',
            'userdel',
        ]
        
        logger.info(f"Security manager initialized with keyword: {self.sudo_keyword}")

    def parse_sudo_keyword(self, user_input: str) -> Tuple[bool, int, Optional[str]]:
        """
        Parse user input for sudo keyword and duration
        
        Args:
            user_input: User input string
        
        Returns:
            Tuple of (is_sudo_keyword, duration_seconds, reason)
        """
        user_lower = user_input.lower().strip()
        
        # Check for exact match with default keyword
        if self.sudo_keyword.lower() in user_lower:
            return True, self.default_sudo_duration, "Default sudo access"
        
        # Check for time-based variants (e.g., "sudo code 300")
        if self.allow_timed_sudo and "sudo code" in user_lower:
            try:
                # Extract time value
                parts = user_lower.split()
                for i, part in enumerate(parts):
                    if part == "code" and i + 1 < len(parts):
                        time_value = int(parts[i + 1])
                        
                        # Validate time (max 3600 seconds = 1 hour)
                        if 0 < time_value <= 3600:
                            return True, time_value, f"Sudo access for {time_value}s"
                        else:
                            logger.warning(f"Invalid sudo time: {time_value}s (max 3600s)")
                            return False, 0, "Invalid time (max 1 hour)"
            except (ValueError, IndexError):
                pass
        
        # Check for custom keyword
        if self.allow_custom_sudo and user_lower == self.sudo_keyword.lower():
            return True, self.default_sudo_duration, "Custom sudo access"
        
        return False, 0, None

    def activate_sudo_mode(self, duration_seconds: Optional[int] = None) -> Tuple[bool, str]:
        """
        Activate sudo mode
        
        Args:
            duration_seconds: Custom duration (if None, use default)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if self.current_session and self.current_session.is_valid():
                remaining = self.current_session.get_remaining_time()
                return False, f"Sudo mode already active for {remaining} more seconds"
            
            duration = duration_seconds or self.default_sudo_duration
            self.current_session = SudoSession(duration)
            
            # Convert to human-readable format
            if duration < 60:
                duration_str = f"{duration} seconds"
            elif duration < 3600:
                duration_str = f"{duration // 60} minutes"
            else:
                duration_str = f"{duration // 3600} hour(s)"
            
            message = f"✓ Sudo mode activated for {duration_str}"
            logger.info(f"Sudo session activated: {duration_str}")
            return True, message
            
        except Exception as e:
            logger.error(f"Sudo activation error: {e}")
            return False, f"Sudo activation failed: {str(e)}"

    def is_sudo_active(self) -> bool:
        """
        Check if sudo mode is currently active
        
        Returns:
            Boolean indicating if sudo is active
        """
        if self.current_session is None:
            return False
        
        return self.current_session.is_valid()

    def get_sudo_status(self) -> str:
        """
        Get current sudo status
        
        Returns:
            Status string
        """
        if not self.current_session:
            return "❌ Sudo mode: INACTIVE"
        
        if not self.current_session.is_valid():
            return "❌ Sudo mode: EXPIRED"
        
        remaining = self.current_session.get_remaining_time()
        
        if remaining < 60:
            return f"⏰ Sudo mode: ACTIVE ({remaining}s remaining)"
        elif remaining < 3600:
            return f"⏰ Sudo mode: ACTIVE ({remaining // 60}m remaining)"
        else:
            return f"⏰ Sudo mode: ACTIVE ({remaining // 3600}h remaining)"

    def check_dangerous_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if command is dangerous
        
        Args:
            command: Command to check
        
        Returns:
            Tuple of (is_dangerous, warning_message)
        """
        command_lower = command.lower()
        
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in command_lower:
                warning = f"⚠️ WARNING: This command is potentially dangerous!\nCommand: {command}"
                logger.warning(f"Dangerous command detected: {command}")
                return True, warning
        
        return False, None

    def execute_with_sudo(self, command: str, require_confirmation: bool = True) -> Tuple[bool, str]:
        """
        Execute command with sudo privilege
        
        Args:
            command: Command to execute
            require_confirmation: Whether to require user confirmation
        
        Returns:
            Tuple of (success, output_or_error)
        """
        # Check if sudo is active
        if not self.is_sudo_active():
            return False, "❌ Sudo mode not active. Say 'sudo code 0' first."
        
        # Check for dangerous commands
        is_dangerous, warning = self.check_dangerous_command(command)
        
        if is_dangerous:
            return False, f"{warning}\n\nThis command will NOT be executed for safety reasons."
        
        try:
            logger.info(f"Executing command with sudo: {command}")
            
            # Execute with sudo
            result = subprocess.run(
                ['sudo'] + command.split(),
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, result.stdout or "✓ Command executed successfully"
            else:
                return False, result.stderr or "Command execution failed"
                
        except subprocess.TimeoutExpired:
            return False, "Command execution timeout"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return False, f"Error: {str(e)}"

    def customize_sudo_keyword(self, new_keyword: str) -> Tuple[bool, str]:
        """
        Customize the sudo keyword
        
        Args:
            new_keyword: New sudo keyword
        
        Returns:
            Tuple of (success, message)
        """
        if not self.allow_custom_sudo:
            return False, "Custom sudo keywords are disabled"
        
        if not new_keyword or len(new_keyword) < 3:
            return False, "Sudo keyword must be at least 3 characters"
        
        old_keyword = self.sudo_keyword
        self.sudo_keyword = new_keyword
        
        logger.info(f"Sudo keyword changed from '{old_keyword}' to '{new_keyword}'")
        return True, f"✓ Sudo keyword changed to: {new_keyword}"

    def get_security_info(self) -> Dict[str, Any]:
        """
        Get current security configuration
        
        Returns:
            Security information dictionary
        """
        return {
            'sudo_keyword': self.sudo_keyword,
            'default_duration': self.default_sudo_duration,
            'allow_custom_sudo': self.allow_custom_sudo,
            'allow_timed_sudo': self.allow_timed_sudo,
            'sudo_active': self.is_sudo_active(),
            'sudo_status': self.get_sudo_status(),
            'current_session': {
                'active': self.current_session.is_valid() if self.current_session else False,
                'remaining_time': self.current_session.get_remaining_time() if self.current_session else 0
            }
        }

    def show_sudo_help(self) -> str:
        """
        Show help for sudo features
        
        Returns:
            Help text
        """
        help_text = f"""
🔐 SUDO MODE - Advanced Security Features

DEFAULT KEYWORD:
  Say: "{self.sudo_keyword}"
  Effect: Activates {self.default_sudo_duration}s (5min) sudo access

TIME-BASED VARIANTS:
  Say: "sudo code 300"   → 5 minutes access
  Say: "sudo code 600"   → 10 minutes access
  Say: "sudo code 1800"  → 30 minutes access
  Say: "sudo code 3600"  → 1 hour access (maximum)

CUSTOM KEYWORD:
  Say: "Customize sudo: unlock the vault"
  Effect: Changes keyword to "unlock the vault"

SAFETY FEATURES:
  ✓ Dangerous commands are blocked
  ✓ Time-limited access windows
  ✓ Session status tracking
  ✓ Automatic timeout

CURRENT STATUS:
  {self.get_sudo_status()}
  Keyword: {self.sudo_keyword}
  Default Duration: {self.default_sudo_duration}s
"""
        return help_text


def main():
    """Test enhanced security manager"""
    config = {
        'security': {
            'sudo_keyword': 'sudo code 0',
            'sudo_mode_duration': 300,
            'allow_custom_sudo': True,
            'allow_timed_sudo': True
        }
    }
    
    security = EnhancedSecurityManager(config)
    
    # Test parsing
    test_inputs = [
        "sudo code 0",
        "sudo code 300",
        "sudo code 1800",
        "hello world"
    ]
    
    for test_input in test_inputs:
        is_sudo, duration, reason = security.parse_sudo_keyword(test_input)
        print(f"Input: '{test_input}'")
        print(f"  Is sudo: {is_sudo}, Duration: {duration}s, Reason: {reason}\n")
    
    # Test activation
    print("Activating sudo...")
    success, msg = security.activate_sudo_mode(600)
    print(msg)
    
    # Test status
    print(f"\nStatus: {security.get_sudo_status()}")
    
    # Test security info
    print(f"\nSecurity config: {security.get_security_info()}")


if __name__ == "__main__":
    main()
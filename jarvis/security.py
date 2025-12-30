"""
Security Module - Handles security checks, sudo sessions, and dangerous command detection
"""

import time
import os
from typing import Optional, List
from datetime import datetime, timedelta
from jarvis.logger import get_logger
import hashlib

logger = get_logger(__name__)


class SudoSession:
    """
    Manages sudo-like privilege escalation with time-limited access
    Uses the "sudo code" keyword for activation
    """

    def __init__(self, duration_seconds: int = 300):
        """
        Initialize sudo session manager
        
        Args:
            duration_seconds: How long sudo mode lasts (default 5 minutes)
        """
        self.duration_seconds = duration_seconds
        self.session_start: Optional[datetime] = None
        self.active = False

    def activate(self) -> bool:
        """
        Activate sudo session
        
        Returns:
            True if activated, False if already active
        """
        if self.active and self.is_valid():
            logger.warning("Sudo session already active")
            return False

        self.session_start = datetime.now()
        self.active = True
        logger.info(f"Sudo session activated for {self.duration_seconds} seconds")
        return True

    def deactivate(self) -> None:
        """Deactivate sudo session"""
        self.active = False
        self.session_start = None
        logger.info("Sudo session deactivated")

    def is_valid(self) -> bool:
        """
        Check if sudo session is still valid
        
        Returns:
            True if session is active and not expired
        """
        if not self.active or not self.session_start:
            return False

        elapsed = (datetime.now() - self.session_start).total_seconds()
        if elapsed > self.duration_seconds:
            self.deactivate()
            return False

        return True

    def remaining_time(self) -> int:
        """
        Get remaining time in sudo session (seconds)
        
        Returns:
            Seconds remaining, or 0 if expired
        """
        if not self.is_valid():
            return 0

        elapsed = (datetime.now() - self.session_start).total_seconds()
        return max(0, int(self.duration_seconds - elapsed))


class SecurityChecker:
    """
    Checks commands for dangerous operations
    """

    def __init__(self, dangerous_keywords: Optional[List[str]] = None):
        """
        Initialize security checker
        
        Args:
            dangerous_keywords: List of keywords to block
        """
        self.dangerous_keywords = dangerous_keywords or [
            "rm -rf",
            "mkfs",
            ":(){:|:&};:",
            "shutdown -h now",
            "reboot",
            "poweroff",
            "dd if=",
            "format c:",
        ]

    def is_dangerous(self, command: str) -> bool:
        """
        Check if command contains dangerous keywords
        
        Args:
            command: Command string to check
        
        Returns:
            True if dangerous, False otherwise
        """
        command_lower = command.lower()
        for keyword in self.dangerous_keywords:
            if keyword.lower() in command_lower:
                logger.warning(f"Dangerous keyword detected: {keyword}")
                return True
        return False

    def check_command(self, command: str, sudo_active: bool = False) -> tuple[bool, str]:
        """
        Check if command is allowed to execute
        
        Args:
            command: Command to check
            sudo_active: Whether sudo session is active
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not command or not command.strip():
            return False, "Empty command"

        if self.is_dangerous(command):
            if sudo_active:
                logger.warning(f"Dangerous command allowed under sudo: {command}")
                return True, "Allowed under sudo session"
            else:
                return False, "Command contains dangerous keywords and sudo not active"

        return True, "Command is safe"


class VoiceProfileManager:
    """
    Manages voice profile registration and verification
    Placeholder for future voice-based authentication
    """

    def __init__(self, profile_dir: str = "./data/voice_profiles"):
        """
        Initialize voice profile manager
        
        Args:
            profile_dir: Directory to store voice profiles
        """
        self.profile_dir = profile_dir
        self._ensure_profile_dir()

    def _ensure_profile_dir(self) -> None:
        """Ensure profile directory exists"""
        os.makedirs(self.profile_dir, exist_ok=True)

    def register_voice_profile(self, user_id: str, audio_samples: List[bytes]) -> bool:
        """
        Register a voice profile for a user
        
        Args:
            user_id: User identifier
            audio_samples: List of audio byte samples
        
        Returns:
            True if registration successful
        """
        logger.info(f"[STUB] Voice profile registration for user: {user_id}")
        # TODO: Implement actual voice profile extraction and storage
        # For now, just create a placeholder
        try:
            profile_file = os.path.join(self.profile_dir, f"{user_id}.profile")
            with open(profile_file, 'w') as f:
                f.write(f"User: {user_id}\n")
                f.write(f"Samples: {len(audio_samples)}\n")
                f.write(f"Registered: {datetime.now().isoformat()}\n")
            logger.info(f"Voice profile saved: {profile_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to register voice profile: {e}")
            return False

    def verify_voice(self, user_id: str, audio_sample: bytes) -> bool:
        """
        Verify a user's voice against their profile
        
        Args:
            user_id: User identifier
            audio_sample: Audio bytes to verify
        
        Returns:
            True if voice matches profile
        """
        logger.info(f"[STUB] Voice verification for user: {user_id}")
        # TODO: Implement actual voice verification
        # For now, just return True
        return True

    def get_profile_path(self, user_id: str) -> str:
        """Get path to user's voice profile"""
        return os.path.join(self.profile_dir, f"{user_id}.profile")

    def profile_exists(self, user_id: str) -> bool:
        """Check if user has a registered profile"""
        return os.path.exists(self.get_profile_path(user_id))


class DownloadValidator:
    """
    Validates downloads before execution
    """

    def __init__(self, max_size_mb: int = 500):
        """
        Initialize download validator
        
        Args:
            max_size_mb: Maximum allowed download size in MB
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_extensions = [
            ".pdf", ".txt", ".jpg", ".png", ".mp3", ".zip",
            ".tar", ".gz", ".mp4", ".mkv", ".exe", ".deb",
            ".rpm", ".pkg", ".dmg", ".iso"
        ]

    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        Validate download URL
        
        Args:
            url: URL to validate
        
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        if not url or not isinstance(url, str):
            return False, "Invalid URL format"

        if not url.startswith(("http://", "https://")):
            return False, "URL must start with http:// or https://"

        return True, "URL is valid"

    def validate_filename(self, filename: str) -> tuple[bool, str]:
        """
        Validate filename for safety
        
        Args:
            filename: Filename to validate
        
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        if not filename or not isinstance(filename, str):
            return False, "Invalid filename"

        if any(char in filename for char in ['/', '\\', '\0', '\n', '\r']):
            return False, "Filename contains invalid characters"

        return True, "Filename is valid"

    def is_allowed_extension(self, filename: str) -> bool:
        """
        Check if file extension is allowed
        
        Args:
            filename: Filename to check
        
        Returns:
            True if extension is allowed
        """
        _, ext = os.path.splitext(filename.lower())
        return ext in self.allowed_extensions


def create_download_log(
    url: str,
    filename: str,
    timestamp: Optional[datetime] = None,
    approved: bool = False
) -> str:
    """
    Create a log entry for a download request
    
    Args:
        url: Download URL
        filename: Target filename
        timestamp: When download was requested
        approved: Whether it was approved
    
    Returns:
        Log entry string
    """
    timestamp = timestamp or datetime.now()
    status = "APPROVED" if approved else "PENDING"
    return f"[{timestamp.isoformat()}] {status} - {filename} from {url}\n"
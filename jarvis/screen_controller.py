"""
Screen Controller Module - GUI automation and screen interactions
Uses pyautogui for cross-desktop compatibility
"""

import pyautogui
import time
from typing import Optional, Tuple, List
from jarvis.logger import get_logger

logger = get_logger(__name__)

# Disable pyautogui fail-safe (no need on Linux for JARVIS)
pyautogui.FAILSAFE = False


class ScreenController:
    """
    Handles GUI automation and screen interactions
    """

    def __init__(self):
        """Initialize screen controller"""
        self.last_action_time = time.time()
        self.action_delay = 0.5  # Delay between actions

    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen resolution
        
        Returns:
            Tuple of (width, height)
        """
        try:
            size = pyautogui.size()
            logger.info(f"Screen size: {size}")
            return size
        except Exception as e:
            logger.error(f"Error getting screen size: {e}")
            return (1920, 1080)  # Default fallback

    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> bool:
        """
        Move mouse to position
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to move (seconds)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Moving mouse to ({x}, {y})")
            pyautogui.moveTo(x, y, duration=duration)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
            return False

    def click(self, x: int = None, y: int = None, button: str = "left") -> bool:
        """
        Click at position
        
        Args:
            x: X coordinate (current position if None)
            y: Y coordinate (current position if None)
            button: Mouse button ('left', 'middle', 'right')
        
        Returns:
            True if successful
        """
        try:
            if x is not None and y is not None:
                self.move_mouse(x, y, duration=0.3)
            logger.info(f"Clicking {button} button")
            pyautogui.click(button=button)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error clicking: {e}")
            return False

    def double_click(self, x: int = None, y: int = None) -> bool:
        """
        Double-click at position
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            True if successful
        """
        try:
            if x is not None and y is not None:
                self.move_mouse(x, y, duration=0.3)
            logger.info("Double-clicking")
            pyautogui.click(clicks=2, interval=0.1)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error double-clicking: {e}")
            return False

    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        Type text using keyboard
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Typing: {text[:50]}...")
            pyautogui.typewrite(text, interval=interval)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """
        Press a keyboard key
        
        Args:
            key: Key name ('enter', 'tab', 'esc', 'space', etc.)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Pressing key: {key}")
            pyautogui.press(key)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return False

    def hotkey(self, *keys: str) -> bool:
        """
        Press multiple keys simultaneously (hotkey)
        
        Args:
            keys: Key names ('ctrl', 'alt', 'shift', 'a', etc.)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Hotkey: {' + '.join(keys)}")
            pyautogui.hotkey(*keys)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error pressing hotkey: {e}")
            return False

    def scroll(self, x: int, y: int, clicks: int = 5, direction: str = "down") -> bool:
        """
        Scroll at position
        
        Args:
            x: X coordinate
            y: Y coordinate
            clicks: Number of scroll clicks
            direction: 'up' or 'down'
        
        Returns:
            True if successful
        """
        try:
            self.move_mouse(x, y, duration=0.3)
            scroll_amount = clicks if direction == "down" else -clicks
            logger.info(f"Scrolling {direction} {clicks} clicks")
            pyautogui.scroll(scroll_amount)
            self._apply_action_delay()
            return True
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False

    def open_app(self, app_name: str) -> bool:
        """
        Open an application by name
        
        Args:
            app_name: Application name or command
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Opening application: {app_name}")
            import subprocess
            subprocess.Popen(app_name, shell=True)
            time.sleep(2)  # Wait for app to start
            return True
        except Exception as e:
            logger.error(f"Error opening app {app_name}: {e}")
            return False

    def find_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Find image on screen and return center position
        
        Args:
            image_path: Path to image file
            confidence: Confidence threshold (0-1)
        
        Returns:
            Tuple of (x, y) if found, None otherwise
        """
        try:
            from PIL import Image
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                logger.info(f"Found image at {center}")
                return center
            else:
                logger.warning(f"Image not found on screen: {image_path}")
                return None
        except Exception as e:
            logger.error(f"Error finding image on screen: {e}")
            return None

    def _apply_action_delay(self) -> None:
        """Apply delay between actions"""
        time.sleep(self.action_delay)

    def set_action_delay(self, delay: float) -> None:
        """Set delay between actions"""
        self.action_delay = max(0, delay)


class WindowManager:
    """
    Manages window operations (minimize, maximize, close, etc.)
    """

    def __init__(self):
        """Initialize window manager"""
        pass

    def activate_window(self, window_title: str) -> bool:
        """
        Activate window by title
        
        Args:
            window_title: Window title to search for
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Activating window: {window_title}")
            # This is a simplified implementation
            # Full implementation would use wmctrl or xdotool
            import subprocess
            subprocess.run(
                ["wmctrl", "-a", window_title],
                check=False
            )
            return True
        except Exception as e:
            logger.error(f"Error activating window: {e}")
            return False

    def minimize_window(self, window_title: str = None) -> bool:
        """Minimize window"""
        try:
            logger.info("Minimizing window")
            import subprocess
            if window_title:
                subprocess.run(["wmctrl", "-r", window_title, "-b", "add,maximized_vert,maximized_horz"], check=False)
            return True
        except Exception as e:
            logger.error(f"Error minimizing window: {e}")
            return False

    def close_window(self, window_title: str = None) -> bool:
        """Close window"""
        try:
            logger.info("Closing window")
            if window_title:
                import subprocess
                subprocess.run(["wmctrl", "-c", window_title], check=False)
            else:
                pyautogui.hotkey('alt', 'F4')
            return True
        except Exception as e:
            logger.error(f"Error closing window: {e}")
            return False
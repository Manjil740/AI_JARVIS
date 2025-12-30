"""
Subtitle Overlay Module - Displays subtitles on screen
Shows recognized text and AI responses with customizable position and styling
"""

import tkinter as tk
from tkinter import font as tkFont
import threading
import time
from typing import Optional
from jarvis.logger import get_logger

logger = get_logger(__name__)


class SubtitleOverlay:
    """
    Creates and manages a floating subtitle window
    Displays at top or bottom center of screen
    """

    def __init__(self, config: dict = None):
        """
        Initialize subtitle overlay
        
        Args:
            config: Configuration dictionary with UI settings
        """
        self.config = config or {}
        ui_config = self.config.get('ui', {})
        
        self.enabled = ui_config.get('subtitles_enabled', True)
        self.position = ui_config.get('subtitle_position', 'bottom')  # 'top' or 'bottom'
        self.font_size = ui_config.get('font_size', 20)
        self.display_duration = ui_config.get('display_duration', 3)
        self.opacity = ui_config.get('background_opacity', 0.8)
        
        self.window = None
        self.label = None
        self.root = None
        self.current_text = ""
        self.hide_timer = None
        
        self._init_window()

    def _init_window(self) -> None:
        """Initialize the overlay window"""
        if not self.enabled:
            return

        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide initially
            
            # Configure window
            self.root.attributes('-type', 'splash')  # Splash screen (always on top, no decoration)
            self.root.attributes('-alpha', 0.95)  # Slight transparency
            
            # Create label for text
            self.label = tk.Label(
                self.root,
                text="",
                font=("Arial", self.font_size),
                fg="white",
                bg="#1a1a1a",
                wraplength=800,
                justify=tk.CENTER,
                padx=20,
                pady=10,
            )
            self.label.pack()
            
            logger.info("Subtitle overlay initialized")
        except Exception as e:
            logger.error(f"Error initializing subtitle overlay: {e}")
            self.enabled = False

    def show(self, text: str) -> None:
        """
        Show subtitle on screen
        
        Args:
            text: Text to display
        """
        if not self.enabled or not self.root:
            return

        try:
            self.current_text = text
            
            # Update label
            self.label.config(text=text)
            
            # Position window
            self._position_window()
            
            # Show window
            self.root.deiconify()
            self.root.update()
            
            # Schedule auto-hide
            if self.hide_timer:
                self.root.after_cancel(self.hide_timer)
            
            self.hide_timer = self.root.after(
                self.display_duration * 1000,
                self.hide
            )
        except Exception as e:
            logger.error(f"Error showing subtitle: {e}")

    def hide(self) -> None:
        """Hide subtitle overlay"""
        if not self.enabled or not self.root:
            return

        try:
            self.root.withdraw()
            self.current_text = ""
        except Exception as e:
            logger.error(f"Error hiding subtitle: {e}")

    def _position_window(self) -> None:
        """Position window at top or bottom center"""
        if not self.root:
            return

        try:
            self.root.update_idletasks()
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Get window dimensions
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # Calculate position (center horizontally)
            x = (screen_width - window_width) // 2
            
            # Position vertically based on config
            if self.position.lower() == 'top':
                y = 50  # 50px from top
            else:
                y = screen_height - window_height - 50  # 50px from bottom
            
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        except Exception as e:
            logger.error(f"Error positioning window: {e}")

    def update_text(self, text: str) -> None:
        """Update text without showing (if already visible)"""
        if not self.enabled or not self.root:
            return

        try:
            self.current_text = text
            self.label.config(text=text)
            self.root.update()
        except Exception as e:
            logger.error(f"Error updating subtitle text: {e}")

    def set_position(self, position: str) -> None:
        """
        Change subtitle position
        
        Args:
            position: 'top' or 'bottom'
        """
        if position.lower() in ['top', 'bottom']:
            self.position = position.lower()
            self._position_window()

    def set_display_duration(self, seconds: int) -> None:
        """Set how long subtitles display"""
        self.display_duration = max(1, seconds)

    def set_font_size(self, size: int) -> None:
        """Set font size"""
        self.font_size = max(10, size)
        if self.label:
            self.label.config(font=("Arial", self.font_size))

    def close(self) -> None:
        """Close and cleanup overlay"""
        if self.hide_timer and self.root:
            try:
                self.root.after_cancel(self.hide_timer)
            except Exception:
                pass
        
        if self.root:
            try:
                self.root.destroy()
            except Exception as e:
                logger.error(f"Error closing subtitle overlay: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


class SubtitleManager:
    """
    Manages subtitle display in a separate thread
    """

    def __init__(self, config: dict = None):
        """
        Initialize subtitle manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.overlay = None
        self._thread = None
        self._running = False

    def start(self) -> None:
        """Start subtitle manager in background thread"""
        if self._running:
            return

        try:
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info("Subtitle manager started")
        except Exception as e:
            logger.error(f"Error starting subtitle manager: {e}")
            self._running = False

    def _run(self) -> None:
        """Run subtitle overlay in event loop"""
        try:
            self.overlay = SubtitleOverlay(self.config)
            if self.overlay.enabled:
                self.overlay.root.mainloop()
        except Exception as e:
            logger.error(f"Error in subtitle manager thread: {e}")
        finally:
            self._running = False

    def show(self, text: str) -> None:
        """Show subtitle text"""
        if self.overlay:
            try:
                self.overlay.show(text)
            except Exception as e:
                logger.error(f"Error showing subtitle: {e}")

    def hide(self) -> None:
        """Hide subtitle"""
        if self.overlay:
            try:
                self.overlay.hide()
            except Exception as e:
                logger.error(f"Error hiding subtitle: {e}")

    def update(self, text: str) -> None:
        """Update subtitle text"""
        if self.overlay:
            try:
                self.overlay.update_text(text)
            except Exception as e:
                logger.error(f"Error updating subtitle: {e}")

    def stop(self) -> None:
        """Stop subtitle manager"""
        self._running = False
        if self.overlay:
            self.overlay.close()
        logger.info("Subtitle manager stopped")
"""
App Intelligence Module - Intelligent app discovery and installation
Researches applications via AI and recommends the best option
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from jarvis.logger import get_logger
from jarvis.ai_backend import AIBackend
from jarvis.utils import load_config

logger = get_logger(__name__)


@dataclass
class AppOption:
    """Represents an available application option"""
    name: str
    description: str
    features: List[str]
    size: str
    ram_required: str
    license: str
    available_in_repos: List[str]
    rating: float
    best_for: str
    complexity: str  # beginner, intermediate, advanced


class AppIntelligenceEngine:
    """
    Intelligent app discovery and recommendation system
    Researches apps, analyzes options, and makes smart recommendations
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize app intelligence engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.ai_backend = AIBackend(self.config)
        self.research_enabled = self.config.get('features', {}).get('app_intelligence', True)
        self.auto_research = self.config.get('features', {}).get('auto_research_apps', True)

    def research_application(self, app_type: str) -> List[AppOption]:
        """
        Research available applications for a given type
        
        Args:
            app_type: Type of application (e.g., "PDF reader", "video editor")
        
        Returns:
            List of AppOption objects
        """
        if not self.research_enabled:
            logger.warning("App intelligence is disabled")
            return []

        logger.info(f"Researching applications for: {app_type}")

        try:
            # Query AI for research
            query = f"""Research and list 5 best {app_type} applications for Linux.
            For each, provide:
            - Name
            - Description (one line)
            - Key features (3-5 bullet points)
            - Size (approximate)
            - RAM required
            - License type
            - Availability in package managers
            - User rating (1-5)
            - Best use case
            - Complexity level (beginner/intermediate/advanced)
            
            Format as JSON array with objects containing these fields.
            Be specific and accurate."""

            response = self.ai_backend.query_sync(query)
            
            if not response:
                logger.error("AI research query failed")
                return []

            response_text = response.get('text', '')
            
            # Parse JSON from response
            try:
                # Extract JSON from response
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    apps_data = json.loads(json_str)
                    
                    # Convert to AppOption objects
                    options = []
                    for app_data in apps_data:
                        option = AppOption(
                            name=app_data.get('name', ''),
                            description=app_data.get('description', ''),
                            features=app_data.get('features', []),
                            size=app_data.get('size', 'Unknown'),
                            ram_required=app_data.get('ram_required', 'Unknown'),
                            license=app_data.get('license', 'Unknown'),
                            available_in_repos=app_data.get('available_in_repos', []),
                            rating=float(app_data.get('rating', 0)),
                            best_for=app_data.get('best_for', ''),
                            complexity=app_data.get('complexity', 'intermediate')
                        )
                        options.append(option)
                    
                    logger.info(f"Found {len(options)} app options")
                    return options
                else:
                    logger.error("Could not find JSON in response")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse app research response: {e}")
                return []

        except Exception as e:
            logger.error(f"App research error: {e}", exc_info=True)
            return []

    def get_recommendation(self, options: List[AppOption]) -> Optional[AppOption]:
        """
        Get AI recommendation from list of options
        
        Args:
            options: List of AppOption objects
        
        Returns:
            Recommended AppOption or None
        """
        if not options:
            return None

        # Simple recommendation based on rating and complexity
        # Prefer higher rated, lower complexity options
        scored_options = [
            (opt, opt.rating - (0.1 if opt.complexity == 'advanced' else 0))
            for opt in options
        ]
        
        best = max(scored_options, key=lambda x: x[1])
        return best[0]

    def format_options_for_user(self, options: List[AppOption], recommendation: Optional[AppOption] = None) -> str:
        """
        Format app options for user display
        
        Args:
            options: List of AppOption objects
            recommendation: Recommended option (if any)
        
        Returns:
            Formatted string for user
        """
        output = []
        
        for i, app in enumerate(options, 1):
            rank = "🥇" if app == recommendation else ("🥈" if i == 2 else "🥉" if i == 3 else f"{i}.")
            
            output.append(f"\n{rank} {app.name}")
            output.append(f"   • Description: {app.description}")
            output.append(f"   • Features: {', '.join(app.features[:3])}")
            output.append(f"   • Size: {app.size}")
            output.append(f"   • RAM: {app.ram_required}")
            output.append(f"   • License: {app.license}")
            output.append(f"   • Rating: {'⭐' * int(app.rating)}")
            output.append(f"   • Best for: {app.best_for}")
        
        if recommendation:
            output.append(f"\n💡 My recommendation: {recommendation.name} ({recommendation.best_for})")
        
        return "\n".join(output)

    def check_availability(self, app_name: str) -> Tuple[bool, List[str]]:
        """
        Check if app is available in package managers
        
        Args:
            app_name: Name of application
        
        Returns:
            Tuple of (available, package_managers)
        """
        import subprocess
        
        available_managers = []
        
        # Check apt (Debian/Ubuntu)
        try:
            result = subprocess.run(['apt-cache', 'search', app_name],
                                  capture_output=True, timeout=5)
            if result.returncode == 0 and app_name.lower() in result.stdout.decode().lower():
                available_managers.append('apt')
        except:
            pass
        
        # Check dnf (Fedora/RHEL)
        try:
            result = subprocess.run(['dnf', 'search', app_name],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                available_managers.append('dnf')
        except:
            pass
        
        # Check pacman (Arch)
        try:
            result = subprocess.run(['pacman', '-Ss', app_name],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                available_managers.append('pacman')
        except:
            pass
        
        # Check zypper (openSUSE)
        try:
            result = subprocess.run(['zypper', 'search', app_name],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                available_managers.append('zypper')
        except:
            pass
        
        return len(available_managers) > 0, available_managers

    def install_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Attempt to install application
        
        Args:
            app_name: Name of application to install
        
        Returns:
            Tuple of (success, message)
        """
        import subprocess
        import platform
        
        try:
            # Detect distro and use appropriate package manager
            distro = platform.linux_distribution()[0].lower() if hasattr(platform, 'linux_distribution') else ''
            
            # Try apt first (most common)
            try:
                logger.info(f"Installing {app_name} via apt")
                result = subprocess.run(['sudo', 'apt', 'install', '-y', app_name],
                                      capture_output=True, timeout=300)
                if result.returncode == 0:
                    return True, f"✓ {app_name} installed successfully!"
            except:
                pass
            
            # Try dnf
            try:
                logger.info(f"Installing {app_name} via dnf")
                result = subprocess.run(['sudo', 'dnf', 'install', '-y', app_name],
                                      capture_output=True, timeout=300)
                if result.returncode == 0:
                    return True, f"✓ {app_name} installed successfully!"
            except:
                pass
            
            # Try pacman
            try:
                logger.info(f"Installing {app_name} via pacman")
                result = subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', app_name],
                                      capture_output=True, timeout=300)
                if result.returncode == 0:
                    return True, f"✓ {app_name} installed successfully!"
            except:
                pass
            
            return False, f"Could not install {app_name}. Try manual installation."
            
        except Exception as e:
            logger.error(f"Installation error: {e}")
            return False, f"Installation failed: {str(e)}"

    def full_workflow(self, app_type: str) -> Tuple[bool, str, Optional[AppOption]]:
        """
        Complete workflow: research → recommend → confirm → install
        
        Args:
            app_type: Type of application needed
        
        Returns:
            Tuple of (success, message, installed_app)
        """
        logger.info(f"Starting app intelligence workflow for: {app_type}")
        
        # Step 1: Research
        logger.info("Step 1: Researching applications...")
        options = self.research_application(app_type)
        
        if not options:
            return False, "No applications found", None
        
        # Step 2: Get recommendation
        recommendation = self.get_recommendation(options)
        
        # Step 3: Format for user
        formatted = self.format_options_for_user(options, recommendation)
        
        return True, formatted, recommendation


def main():
    """Test app intelligence engine"""
    config = load_config()
    engine = AppIntelligenceEngine(config)
    
    # Test research
    success, options, recommendation = engine.full_workflow("PDF reader")
    
    if success:
        print(options)
        if recommendation:
            print(f"\nUser said: Yes")
            install_success, message = engine.install_application(recommendation.name)
            print(message)
    else:
        print(f"Error: {options}")


if __name__ == "__main__":
    main()
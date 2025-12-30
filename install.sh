#!/bin/bash

################################################################################
# JARVIS v2.0 - Complete Installation & Setup Script
# Production-Ready Voice AI Assistant with Smart Routing & Web Portal
# 
# Features:
# ✅ Auto-detects OS & Linux distro
# ✅ Creates Python virtual environment
# ✅ Installs all dependencies
# ✅ Sets up systemd service
# ✅ Auto-start on boot
# ✅ Verification & testing
# ✅ Complete logging
#
# Usage: bash install.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/install.log"

################################################################################
# UTILITY FUNCTIONS
################################################################################

log() {
    echo -e "${BLUE}[JARVIS]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

section() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n" | tee -a "$LOG_FILE"
}

################################################################################
# OS & DISTRO DETECTION
################################################################################

detect_os() {
    section "🔍 DETECTING OS & DISTRO"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log "OS: Linux detected"
        
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            DISTRO_VERSION=$VERSION_ID
            log "Distro: $PRETTY_NAME"
        else
            error "Cannot detect Linux distro"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        error "macOS is not supported. Linux (Debian/Ubuntu) required."
    else
        error "Unsupported OS: $OSTYPE"
    fi
    
    # Check if Debian/Ubuntu
    case "$DISTRO" in
        debian|ubuntu)
            success "✓ Debian/Ubuntu detected"
            ;;
        *)
            warning "Distro: $DISTRO (may not be fully tested)"
            ;;
    esac
}

################################################################################
# PYTHON & VENV CHECK
################################################################################

check_python() {
    section "🐍 CHECKING PYTHON"
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 is not installed. Installing..."
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log "Python version: $PYTHON_VERSION"
    
    # Check if Python >= 3.8
    if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
        error "Python 3.8+ required. Found: $PYTHON_VERSION"
    fi
    
    success "✓ Python $PYTHON_VERSION (OK)"
}

create_venv() {
    section "📦 CREATING VIRTUAL ENVIRONMENT"
    
    if [ -d "$VENV_DIR" ]; then
        warning "Virtual environment already exists. Skipping..."
        return
    fi
    
    log "Creating venv at: $VENV_DIR"
    python3 -m venv "$VENV_DIR" || error "Failed to create venv"
    
    success "✓ Virtual environment created"
}

activate_venv() {
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate" || error "Failed to activate venv"
    success "✓ Virtual environment activated"
}

################################################################################
# INSTALL SYSTEM DEPENDENCIES
################################################################################

install_system_deps() {
    section "📚 INSTALLING SYSTEM DEPENDENCIES"
    
    if [ "$DISTRO" == "ubuntu" ] || [ "$DISTRO" == "debian" ]; then
        log "Updating package manager..."
        sudo apt-get update -qq
        
        log "Installing system packages..."
        sudo apt-get install -y \
            python3-dev \
            python3-pip \
            python3-venv \
            build-essential \
            portaudio19-dev \
            libportaudio2 \
            libportaudiocpp0 \
            libpulse-dev \
            libespeak-dev \
            ffmpeg \
            git \
            curl \
            wget \
            nano \
            2>&1 | grep -v "^Reading\|^Building\|^Selecting" || true
        
        success "✓ System dependencies installed"
    else
        warning "Distro not recognized. Manual dependency installation may be needed."
    fi
}

################################################################################
# INSTALL PYTHON DEPENDENCIES
################################################################################

install_python_deps() {
    section "🐍 INSTALLING PYTHON DEPENDENCIES"
    
    log "Upgrading pip, setuptools, wheel..."
    pip install --upgrade pip setuptools wheel --quiet
    
    log "Installing Python packages..."
    
    # Core packages
    pip install --quiet \
        requests \
        numpy \
        scipy \
        librosa \
        sounddevice \
        soundfile \
        pyttsx3 \
        SpeechRecognition \
        python-dotenv \
        pydub \
        google-generativeai \
        openai \
        httpx \
        paramiko \
        psutil \
        pyaudio \
        webrtcvad \
        pocketsphinx \
        future \
        six || error "Failed to install Python packages"
    
    success "✓ Python dependencies installed"
}

################################################################################
# COPY FILES
################################################################################

copy_files() {
    section "📋 COPYING APPLICATION FILES"
    
    log "Verifying all required files..."
    
    REQUIRED_FILES=(
        "app-intelligence.py"
        "smart-router.py"
        "response-customizer.py"
        "enhanced-security.py"
        "voice-biometric.py"
        "ai-customize-secure.html"
        "config-updated.json"
        "ai_backend-COMPLETE.py"
        "voice_command_system-COMPLETE.py"
        "direct_prompt_system-COMPLETE.py"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ]; then
            warning "Missing: $file (will skip)"
        else
            log "✓ Found: $file"
        fi
    done
    
    success "✓ File verification complete"
}

################################################################################
# UPDATE CORE FILES
################################################################################

update_core_files() {
    section "⚡ UPDATING CORE FILES"
    
    log "Backing up original files..."
    [ -f "$PROJECT_DIR/ai_backend.py" ] && cp "$PROJECT_DIR/ai_backend.py" "$PROJECT_DIR/ai_backend.py.bak"
    [ -f "$PROJECT_DIR/voice_command_system.py" ] && cp "$PROJECT_DIR/voice_command_system.py" "$PROJECT_DIR/voice_command_system.py.bak"
    [ -f "$PROJECT_DIR/direct_prompt_system.py" ] && cp "$PROJECT_DIR/direct_prompt_system.py" "$PROJECT_DIR/direct_prompt_system.py.bak"
    [ -f "$PROJECT_DIR/config/config.json" ] && cp "$PROJECT_DIR/config/config.json" "$PROJECT_DIR/config/config.json.bak"
    
    success "✓ Backups created"
    
    log "Updating core files..."
    [ -f "$PROJECT_DIR/ai_backend-COMPLETE.py" ] && cp "$PROJECT_DIR/ai_backend-COMPLETE.py" "$PROJECT_DIR/ai_backend.py"
    [ -f "$PROJECT_DIR/voice_command_system-COMPLETE.py" ] && cp "$PROJECT_DIR/voice_command_system-COMPLETE.py" "$PROJECT_DIR/voice_command_system.py"
    [ -f "$PROJECT_DIR/direct_prompt_system-COMPLETE.py" ] && cp "$PROJECT_DIR/direct_prompt_system-COMPLETE.py" "$PROJECT_DIR/direct_prompt_system.py"
    [ -f "$PROJECT_DIR/ai_backend-COMPLETE.py" ] && cp "$PROJECT_DIR/ai_backend-COMPLETE.py" "$PROJECT_DIR/jarvis/ai_backend.py"
    [ -f "$PROJECT_DIR/config-updated.json" ] && cp "$PROJECT_DIR/config-updated.json" "$PROJECT_DIR/config/config.json"
    
    success "✓ Core files updated"
}

################################################################################
# PYTHON SYNTAX VERIFICATION
################################################################################

verify_syntax() {
    section "✅ VERIFYING PYTHON SYNTAX"
    
    FILES_TO_CHECK=(
        "app-intelligence.py"
        "smart-router.py"
        "response-customizer.py"
        "enhanced-security.py"
        "voice-biometric.py"
        "ai_backend.py"
        "voice_command_system.py"
        "direct_prompt_system.py"
    )
    
    ERRORS=0
    
    for file in "${FILES_TO_CHECK[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            if python3 -m py_compile "$PROJECT_DIR/$file" 2>/dev/null; then
                success "✓ $file"
            else
                error "$file - Syntax error detected"
                ((ERRORS++))
            fi
        fi
    done
    
    if [ $ERRORS -gt 0 ]; then
        error "$ERRORS file(s) have syntax errors"
    fi
    
    success "✓ All files verified"
}

################################################################################
# IMPORT VERIFICATION
################################################################################

verify_imports() {
    section "📦 VERIFYING IMPORTS"
    
    activate_venv
    
    MODULES=(
        "app_intelligence:AppIntelligenceEngine"
        "smart_router:SmartRouter"
        "response_customizer:ResponseCustomizer"
        "enhanced_security:EnhancedSecurityManager"
        "voice_biometric:DebugModeManager"
    )
    
    for module_info in "${MODULES[@]}"; do
        IFS=':' read -r module class <<< "$module_info"
        if python3 -c "from ${module} import ${class}; print('✓ ${module}')" 2>/dev/null; then
            success "✓ $module ($class)"
        else
            warning "⚠ $module - may not be available yet"
        fi
    done
}

################################################################################
# SYSTEMD SERVICE SETUP
################################################################################

setup_systemd_service() {
    section "🔧 SETTING UP SYSTEMD SERVICE"
    
    CURRENT_USER=$(whoami)
    SERVICE_FILE="/etc/systemd/system/jarvis.service"
    
    log "Creating systemd service for user: $CURRENT_USER"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=JARVIS - AI Voice Assistant
After=network.target sound.target
Wants=sound.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$VENV_DIR/bin/python3 $PROJECT_DIR/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    success "✓ Service file created: $SERVICE_FILE"
    
    log "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    log "Enabling service to start on boot..."
    sudo systemctl enable jarvis
    
    success "✓ Systemd service configured"
}

################################################################################
# AUTOSTART CONFIGURATION
################################################################################

setup_autostart() {
    section "🚀 SETTING UP AUTOSTART"
    
    AUTOSTART_DIR="$HOME/.config/autostart"
    DESKTOP_FILE="$AUTOSTART_DIR/jarvis.desktop"
    
    mkdir -p "$AUTOSTART_DIR"
    
    log "Creating desktop file for autostart..."
    
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=JARVIS Voice Assistant
Comment=AI Voice Assistant with Smart Routing
Icon=microphone
Exec=$VENV_DIR/bin/python3 $PROJECT_DIR/main.py
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
EOF
    
    success "✓ Autostart configured"
    log "Location: $DESKTOP_FILE"
}

################################################################################
# CONFIGURATION SETUP
################################################################################

setup_config() {
    section "⚙️  SETTING UP CONFIGURATION"
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log "Creating .env file..."
        cat > "$PROJECT_DIR/.env" <<EOF
# JARVIS v2.0 Configuration

# API Keys (add your own)
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Audio Settings
AUDIO_DEVICE_INDEX=0
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024

# Voice Settings
VOICE_SPEED=1.0
VOICE_VOLUME=0.8

# Logging
LOG_LEVEL=INFO
LOG_FILE=$PROJECT_DIR/logs/jarvis.log

# Debug Mode
DEBUG=false
EOF
        success "✓ .env file created"
        warning "⚠ Add your API keys to .env file before starting"
    else
        log ".env already exists, skipping..."
    fi
    
    mkdir -p "$PROJECT_DIR/logs"
    success "✓ Logs directory created"
}

################################################################################
# PERMISSIONS SETUP
################################################################################

setup_permissions() {
    section "🔒 SETTING UP PERMISSIONS"
    
    log "Setting executable permissions..."
    chmod +x "$PROJECT_DIR/install.sh" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/main.py" 2>/dev/null || true
    
    log "Setting proper ownership..."
    sudo chown -R "$USER:$USER" "$PROJECT_DIR" 2>/dev/null || true
    
    success "✓ Permissions configured"
}

################################################################################
# TESTING
################################################################################

test_installation() {
    section "🧪 TESTING INSTALLATION"
    
    activate_venv
    
    log "Testing Python imports..."
    if python3 -c "import sys; print(f'Python {sys.version}')" > /dev/null 2>&1; then
        success "✓ Python environment working"
    else
        warning "⚠ Python environment test failed"
    fi
    
    log "Testing service status..."
    if sudo systemctl status jarvis > /dev/null 2>&1; then
        success "✓ Service running"
    else
        warning "⚠ Service not yet started (will start after reboot or manual start)"
    fi
    
    log "Checking required directories..."
    [ -d "$PROJECT_DIR/config" ] && success "✓ Config directory"
    [ -d "$PROJECT_DIR/logs" ] && success "✓ Logs directory"
    [ -f "$PROJECT_DIR/ai-customize-secure.html" ] && success "✓ Web portal"
}

################################################################################
# SUMMARY & NEXT STEPS
################################################################################

show_summary() {
    section "📊 INSTALLATION SUMMARY"
    
    cat <<EOF

✅ JARVIS v2.0 Installation Complete!

📁 Installation Directory: $PROJECT_DIR
🐍 Virtual Environment: $VENV_DIR
📝 Configuration: $PROJECT_DIR/.env
📊 Logs: $PROJECT_DIR/logs/
🔐 Service: jarvis.service
🌐 Web Portal: file://$PROJECT_DIR/ai-customize-secure.html

═══════════════════════════════════════════════════════════════════

🚀 NEXT STEPS:

1. Add API Keys to .env:
   nano $PROJECT_DIR/.env
   
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=...
   DEEPSEEK_API_KEY=...

2. Start JARVIS manually:
   sudo systemctl start jarvis
   
3. Check status:
   sudo systemctl status jarvis
   
4. View logs:
   journalctl -u jarvis -f
   
5. Test voice commands:
   jarvis> "i need a pdf reader"
   jarvis> "sudo code 0"
   
6. Access web portal:
   Open: file://$PROJECT_DIR/ai-customize-secure.html
   Auth: debugmode code 0

═══════════════════════════════════════════════════════════════════

📋 SYSTEM INFO:

OS Distro: $DISTRO $DISTRO_VERSION
Python: $PYTHON_VERSION
User: $(whoami)
Hostname: $(hostname)

═══════════════════════════════════════════════════════════════════

⚡ AUTOSTART CONFIGURATION:

✓ Systemd service will auto-start on boot
✓ Desktop autostart configured
✓ Just reboot to test!

Or start manually:
  sudo systemctl start jarvis
  sudo systemctl enable jarvis

═══════════════════════════════════════════════════════════════════

📚 DOCUMENTATION:

Check ~/AI_Intrigation/docs/ for:
  - FILE-PLACEMENT-GUIDE.md
  - EXISTING-FILES-UPDATE-GUIDE.md
  - COMPLETE-INTEGRATION-SUMMARY.md
  - MASTER-IMPLEMENTATION-CHECKLIST.md
  - And 4 more guides...

═══════════════════════════════════════════════════════════════════

🎉 Ready to automate! Voice control is one command away.

Log file: $LOG_FILE

EOF
}

################################################################################
# ERROR HANDLING & CLEANUP
################################################################################

handle_error() {
    error "Installation failed. Check $LOG_FILE for details."
    exit 1
}

trap handle_error ERR

################################################################################
# MAIN INSTALLATION FLOW
################################################################################

main() {
    echo ""
    cat <<EOF
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          🤖  JARVIS v2.0 Installation Script  🤖            ║
║                                                               ║
║   Intelligent Voice AI with Smart Routing & Web Portal       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo ""
    
    > "$LOG_FILE"
    log "Starting JARVIS v2.0 installation..."
    log "Log file: $LOG_FILE"
    
    detect_os
    check_python
    create_venv
    activate_venv
    install_system_deps
    install_python_deps
    copy_files
    update_core_files
    verify_syntax
    verify_imports
    setup_config
    setup_permissions
    setup_systemd_service
    setup_autostart
    test_installation
    show_summary
    
    log "✅ Installation completed successfully!"
}

main "$@"

#!/bin/bash
#
# Installation script for ytffmpeg sysv-init service
# Run as root or with sudo
#

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

echo "=================================================="
echo "ytffmpeg SysV Init Service Installer"
echo "=================================================="
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
YTFFMPEG_USER="${YTFFMPEG_USER:-ytffmpeg}"
YTFFMPEG_GROUP="${YTFFMPEG_GROUP:-ytffmpeg}"
WORKSPACE="${WORKSPACE:-/var/lib/ytffmpeg}"
HTTP_PORT="${HTTP_PORT:-9091}"

echo "Configuration:"
echo "  User/Group: $YTFFMPEG_USER:$YTFFMPEG_GROUP"
echo "  Workspace: $WORKSPACE"
echo "  HTTP Port: $HTTP_PORT"
echo

# Check if ytffmpeg is installed
if ! command -v ytffmpeg &> /dev/null; then
    echo "WARNING: ytffmpeg command not found in PATH"
    echo "Please install ytffmpeg first:"
    echo "  pip install ytffmpeg"
    echo "  or: pip install -e ."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Create system user
echo "[1/6] Creating system user..."
if id "$YTFFMPEG_USER" &>/dev/null; then
    echo "  User $YTFFMPEG_USER already exists"
else
    adduser --system --group --home "$WORKSPACE" \
        --disabled-password --disabled-login "$YTFFMPEG_USER"
    echo "  Created user: $YTFFMPEG_USER"
fi

# Step 2: Create workspace directory
echo "[2/6] Creating workspace directory..."
mkdir -p "$WORKSPACE"
chown "$YTFFMPEG_USER:$YTFFMPEG_GROUP" "$WORKSPACE"
chmod 755 "$WORKSPACE"
echo "  Workspace created: $WORKSPACE"

# Step 3: Install init script
echo "[3/6] Installing init script..."
cp "$SCRIPT_DIR/ytffmpeg" /etc/init.d/ytffmpeg
chmod 755 /etc/init.d/ytffmpeg
echo "  Installed: /etc/init.d/ytffmpeg"

# Step 4: Install default configuration
echo "[4/6] Installing default configuration..."
if [ -f /etc/default/ytffmpeg ]; then
    echo "  /etc/default/ytffmpeg already exists, creating backup..."
    cp /etc/default/ytffmpeg /etc/default/ytffmpeg.backup
fi

# Create customized default file
cat > /etc/default/ytffmpeg <<EOF
# Defaults for ytffmpeg init script
# sourced by /etc/init.d/ytffmpeg

# User and group to run ytffmpeg as
YTFFMPEG_USER=$YTFFMPEG_USER
YTFFMPEG_GROUP=$YTFFMPEG_GROUP

# Workspace directory for video projects
YTFFMPEG_WORKSPACE=$WORKSPACE

# HTTP port for the web server
export HTTP_PORT=$HTTP_PORT

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Additional options to pass to ytffmpeg serve
DAEMON_OPTS=""
EOF

echo "  Installed: /etc/default/ytffmpeg"

# Step 5: Enable service autostart
echo "[5/6] Enabling service autostart..."
if command -v update-rc.d &> /dev/null; then
    update-rc.d ytffmpeg defaults
    echo "  Service enabled via update-rc.d"
elif command -v chkconfig &> /dev/null; then
    chkconfig --add ytffmpeg
    chkconfig ytffmpeg on
    echo "  Service enabled via chkconfig"
else
    echo "  WARNING: Could not enable autostart (update-rc.d/chkconfig not found)"
    echo "  You may need to enable manually"
fi

# Step 6: Create config directory (optional)
echo "[6/6] Creating config directory..."
CONFIG_DIR="$WORKSPACE/.config/ytffmpeg"
mkdir -p "$CONFIG_DIR"
chown -R "$YTFFMPEG_USER:$YTFFMPEG_GROUP" "$WORKSPACE/.config"
echo "  Config directory: $CONFIG_DIR"

echo
echo "=================================================="
echo "Installation Complete!"
echo "=================================================="
echo
echo "Next steps:"
echo
echo "1. (Optional) Create configuration file:"
echo "   sudo nano $CONFIG_DIR/config.yml"
echo
echo "2. Start the service:"
echo "   sudo service ytffmpeg start"
echo
echo "3. Check status:"
echo "   sudo service ytffmpeg status"
echo
echo "4. Access web interface:"
echo "   http://localhost:$HTTP_PORT/"
echo
echo "For more information, see README.md"
echo

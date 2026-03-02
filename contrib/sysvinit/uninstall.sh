#!/bin/bash
#
# Uninstallation script for ytffmpeg sysv-init service
# Run as root or with sudo
#

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Usage: sudo ./uninstall.sh"
    exit 1
fi

echo "=================================================="
echo "ytffmpeg SysV Init Service Uninstaller"
echo "=================================================="
echo

# Warning
echo "WARNING: This will remove the ytffmpeg service."
echo "Video files in /var/lib/ytffmpeg will NOT be deleted automatically."
echo
read -p "Continue with uninstallation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Step 1: Stop the service
echo "[1/4] Stopping ytffmpeg service..."
if service ytffmpeg status &>/dev/null; then
    service ytffmpeg stop
    echo "  Service stopped"
else
    echo "  Service not running"
fi

# Step 2: Disable autostart
echo "[2/4] Disabling service autostart..."
if command -v update-rc.d &> /dev/null; then
    update-rc.d -f ytffmpeg remove
    echo "  Autostart disabled via update-rc.d"
elif command -v chkconfig &> /dev/null; then
    chkconfig ytffmpeg off
    chkconfig --del ytffmpeg
    echo "  Autostart disabled via chkconfig"
else
    echo "  WARNING: Could not disable autostart"
fi

# Step 3: Remove service files
echo "[3/4] Removing service files..."
rm -f /etc/init.d/ytffmpeg
echo "  Removed: /etc/init.d/ytffmpeg"

if [ -f /etc/default/ytffmpeg ]; then
    rm -f /etc/default/ytffmpeg
    echo "  Removed: /etc/default/ytffmpeg"
fi

if [ -f /var/run/ytffmpeg.pid ]; then
    rm -f /var/run/ytffmpeg.pid
    echo "  Removed: /var/run/ytffmpeg.pid"
fi

# Step 4: Ask about user and data removal
echo "[4/4] Cleanup options..."
echo

read -p "Remove ytffmpeg system user? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if id ytffmpeg &>/dev/null; then
        deluser ytffmpeg
        echo "  Removed user: ytffmpeg"
    fi
fi

read -p "Remove workspace directory /var/lib/ytffmpeg? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d /var/lib/ytffmpeg ]; then
        echo "  WARNING: This will delete all video files and projects!"
        read -p "Are you SURE? (type 'yes' to confirm) " -r
        echo
        if [[ $REPLY == "yes" ]]; then
            rm -rf /var/lib/ytffmpeg
            echo "  Removed: /var/lib/ytffmpeg"
        else
            echo "  Workspace preserved: /var/lib/ytffmpeg"
        fi
    fi
else
    echo "  Workspace preserved: /var/lib/ytffmpeg"
fi

echo
echo "=================================================="
echo "Uninstallation Complete!"
echo "=================================================="
echo
echo "The ytffmpeg service has been removed."
echo
if [ -d /var/lib/ytffmpeg ]; then
    echo "Video files are preserved in: /var/lib/ytffmpeg"
    echo "Remove manually with: sudo rm -rf /var/lib/ytffmpeg"
fi
echo

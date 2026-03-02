# ytffmpeg SysV Init Scripts

This directory contains init scripts for running ytffmpeg as a system service on Devuan and other sysv-init based systems.

## Installation

### 1. Install ytffmpeg

First, ensure ytffmpeg is installed system-wide:

```bash
sudo pip install ytffmpeg
# or for development:
sudo pip install -e .
```

### 2. Create System User

Create a dedicated user and group for running the service:

```bash
sudo adduser --system --group --home /var/lib/ytffmpeg \
    --disabled-password --disabled-login ytffmpeg
```

### 3. Create Workspace Directory

```bash
sudo mkdir -p /var/lib/ytffmpeg
sudo chown ytffmpeg:ytffmpeg /var/lib/ytffmpeg
sudo chmod 755 /var/lib/ytffmpeg
```

### 4. Install Init Script

```bash
# Copy the init script
sudo cp ytffmpeg /etc/init.d/ytffmpeg
sudo chmod 755 /etc/init.d/ytffmpeg

# Copy the default configuration
sudo cp ytffmpeg.default /etc/default/ytffmpeg

# Make the service start automatically at boot
sudo update-rc.d ytffmpeg defaults
```

### 5. Configure (Optional)

Edit `/etc/default/ytffmpeg` to customize:

```bash
sudo nano /etc/default/ytffmpeg
```

Available options:

- `YTFFMPEG_USER` - User to run as (default: ytffmpeg)
- `YTFFMPEG_GROUP` - Group to run as (default: ytffmpeg)
- `YTFFMPEG_WORKSPACE` - Directory for video projects (default: /var/lib/ytffmpeg)
- `HTTP_PORT` - Web server port (default: 9091)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

### 6. Create Configuration File (Optional)

Create `/var/lib/ytffmpeg/.config/ytffmpeg/config.yml`:

```bash
sudo mkdir -p /var/lib/ytffmpeg/.config/ytffmpeg
sudo nano /var/lib/ytffmpeg/.config/ytffmpeg/config.yml
```

Example configuration:

```yaml
ytffmpeg:
  workspace: /var/lib/ytffmpeg
  http_port: 9091
  language: en
  languages: [en, es, fr]
  subtitles: true
  device: cuda
  webroot: /usr/share/ytffmpeg/web
```

```bash
sudo chown -R ytffmpeg:ytffmpeg /var/lib/ytffmpeg/.config
```

## Usage

### Start the Service

```bash
sudo service ytffmpeg start
```

### Stop the Service

```bash
sudo service ytffmpeg stop
```

### Restart the Service

```bash
sudo service ytffmpeg restart
```

### Check Status

```bash
sudo service ytffmpeg status
```

### View Logs

Since the service runs in the background, check syslog for output:

```bash
sudo tail -f /var/log/syslog | grep ytffmpeg
```

Or use journalctl if available:

```bash
sudo journalctl -u ytffmpeg -f
```

## Access the Web Interface

Once the service is running, access the web interface at:

```plain
http://localhost:9091/
```

Or from another machine (replace with server IP):

```plain
http://192.168.1.100:9091/
```

## Troubleshooting

### Service won't start

Check permissions:

```bash
ls -la /var/lib/ytffmpeg
sudo -u ytffmpeg ytffmpeg serve  # Test as service user
```

Check if port is available:

```bash
sudo netstat -tulpn | grep 9091
```

### Permission denied errors

Ensure the ytffmpeg user owns the workspace:

```bash
sudo chown -R ytffmpeg:ytffmpeg /var/lib/ytffmpeg
```

### Command not found

Verify ytffmpeg is installed and in PATH:

```bash
which ytffmpeg
sudo -u ytffmpeg which ytffmpeg
```

If not found, create a symlink:

```bash
sudo ln -s /usr/local/bin/ytffmpeg /usr/bin/ytffmpeg
```

### GPU access issues

Add the ytffmpeg user to the video group for GPU access:

```bash
sudo usermod -a -G video ytffmpeg
```

## Uninstallation

Remove the service:

```bash
# Stop the service
sudo service ytffmpeg stop

# Disable autostart
sudo update-rc.d -f ytffmpeg remove

# Remove files
sudo rm /etc/init.d/ytffmpeg
sudo rm /etc/default/ytffmpeg

# Optionally remove user and data
sudo deluser ytffmpeg
sudo rm -rf /var/lib/ytffmpeg
```

## File Locations

- **Init script**: `/etc/init.d/ytffmpeg`
- **Default config**: `/etc/default/ytffmpeg`
- **User config**: `/var/lib/ytffmpeg/.config/ytffmpeg/config.yml`
- **Workspace**: `/var/lib/ytffmpeg/`
- **PID file**: `/var/run/ytffmpeg.pid`
- **Web interface**: `http://localhost:9091`

## Security Notes

- The service runs as an unprivileged user (`ytffmpeg`)
- Consider using a firewall to restrict access to port 9091
- For production use, run behind a reverse proxy (nginx, Apache) with SSL
- The web interface has no authentication by default - add auth via proxy

## Support

For issues or questions:

- [GitHub Issues](https://github.com/markizano/ytffmpeg/issues)
- Documentation: `ytffmpeg --help`

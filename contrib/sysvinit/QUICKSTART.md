# ytffmpeg SysV Init - Quick Start

Quick reference for installing and managing ytffmpeg as a Devuan service.

## One-Line Install

```bash
cd contrib/sysvinit && sudo ./install.sh
```

## Manual Installation (5 Steps)

```bash
# 1. Create system user
sudo adduser --system --group --home /var/lib/ytffmpeg \
    --disabled-password --disabled-login ytffmpeg

# 2. Create workspace
sudo mkdir -p /var/lib/ytffmpeg
sudo chown ytffmpeg:ytffmpeg /var/lib/ytffmpeg

# 3. Install service
sudo cp ytffmpeg /etc/init.d/ytffmpeg
sudo cp ytffmpeg.default /etc/default/ytffmpeg
sudo chmod 755 /etc/init.d/ytffmpeg

# 4. Enable autostart
sudo update-rc.d ytffmpeg defaults

# 5. Start service
sudo service ytffmpeg start
```

## Service Management

```bash
# Start
sudo service ytffmpeg start

# Stop
sudo service ytffmpeg stop

# Restart
sudo service ytffmpeg restart

# Status
sudo service ytffmpeg status
```

## Access Web Interface

```
http://localhost:9091/
```

## Configuration

Edit `/etc/default/ytffmpeg`:

```bash
YTFFMPEG_USER=ytffmpeg
YTFFMPEG_GROUP=ytffmpeg
YTFFMPEG_WORKSPACE=/var/lib/ytffmpeg
export HTTP_PORT=9091
export LOG_LEVEL=INFO
```

## Uninstall

```bash
sudo ./uninstall.sh
```

## Troubleshooting

```bash
# Check logs
sudo tail -f /var/log/syslog | grep ytffmpeg

# Check if port is available
sudo netstat -tulpn | grep 9091

# Test as service user
sudo -u ytffmpeg ytffmpeg serve

# Check permissions
ls -la /var/lib/ytffmpeg

# Add GPU access
sudo usermod -a -G video ytffmpeg
```

## Files

| File | Location |
|------|----------|
| Init script | `/etc/init.d/ytffmpeg` |
| Default config | `/etc/default/ytffmpeg` |
| User config | `/var/lib/ytffmpeg/.config/ytffmpeg/config.yml` |
| Workspace | `/var/lib/ytffmpeg/` |
| PID file | `/var/run/ytffmpeg.pid` |

## See Also

- **Full documentation**: See `README.md`
- **Project docs**: See main `CLAUDE.md` and `doc/WEBSERVER.md`

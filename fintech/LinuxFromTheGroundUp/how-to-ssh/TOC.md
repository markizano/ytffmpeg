
# Installing the Package
- In Debian
- In RHEL
- In Gentoo

# SSH As a Server
- Configuration.
- Options.
- Service File Locations in sysvinit, OpenRC and systemd.

# SSH As a Client
- Configuration
- Options
- Networking capabilities with SSH

# Permissions
- .ssh must be 0700/rwx --- ---
- .ssh/id_*/private-keys must be read-only (0400-0600/r-- --- ---)
- files in .ssh other than private keys may have any permissions, but ownership and read-write to owner is suggested/best-security practice.

# SSH Agent
- What is it?
- How to bypass passphrase on each login using the agent.

# Networking
- Port forwarding.
- SOCKS5 proxy.
- X11 Forwarding
- 


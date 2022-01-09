Hello and welcome to my blog. If you are finding this page, then you might be in a similar 
situation I found myself when I wanted to share audio with different apps if they were being used 
by different user accounts on your local *nix machine when using Pulse audio.

Credits to [Eli Billauer](http://billauer.co.il/blog/2014/01/pa-multiple-users/) and 
[Dhole](https://dhole.github.io/post/pulseaudio_multiple_users/) for the configuration directives I 
needed to make this possible.

# The Problem
I have multiple user accounts on my system that run various apps, like my web browser, chat apps, 
email and more. I don't like everything running as myself and try to create a user account with 
just enough privileges to do what it needs to do.

Pulseaudio (herein "Pulse") runs as myself when my desktop environment starts. Apps that run 
normally need to connect to Pulse in some fashion in order to listen to the microphone or play 
audio on the speakers. When the apps all run as the logged in user, this works great. When the apps 
run as someone else, this doesn't work or is inconsistent in behaviour.

# The Scenario
I have a user account `chrome` that is dedicated to the browser `/usr/bin/google-chrome-stable`. 
The browser will run as this account instead of myself and has just enough permissions to render on 
the screen and have basic access to some files on the filesystem (albeit, as the unprivileged 
account).

How do I make it possible to render sound and grant access to the mic when necessary to chrome?

# The Solution
I use local UNIX sockets to allow applications to talk to Pulse and the system behaves. I also 
discovered you DO NOT need to modify the system configuration files in `/etc`.

There's a few configuration files and directives that are used and will be laid out here.

## Server Configuration
As the user who runs Pulse (e.g. creates the server):

- Create `~/.pulse` if it doesn't exist already.
- Create and populate `~/.pulse/default.pa` with the content as described below in the block of configuration.
 - Please note: Pulse will look for local configurations before global configs and will stop looking
 for additional files once it finds a match. The configuration is not a layered configuration in that
 `/etc` is applied first, then local configuration overrides those values. If a local file is present,
 it should include all dependencies and global configuration files or else you could end up with a
 misconfigured setup.
- Restart Pulse. Can use `pulseaudio -k && pulseaudio -D`. Please consult your distribution's
documentation if the mechanism to start Pulse are different for you.
- Personally, I had to `chmod o-rwx /tmp/pulse-server` (aka `chmod 770 /tmp/pulse-server`) to remove
access to the socket outside of me and those part of the `audio` group I wanted apps to share if
they were going to be using audio streams.

Pulse may run as yourself or a dedicated user just for dealing with sound.


`~/.pulse/default.pa`:
```

.include /etc/pulse/default.pa

#load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1

### Load several protocols
load-module module-dbus-protocol
.ifexists module-esound-protocol-unix.so
load-module module-esound-protocol-unix
.endif
load-module module-native-protocol-unix auth-group=audio socket=/tmp/pulse-server

```

## Client Configuration
As someone who will connect to Pulse and attempt to interact with the speakers and/or microphone, you'll
need to include this configuration in every users' home directory under `~/.pulse/client.conf`:

```
# Unix socket method
default-server = unix:/tmp/pulse-server
enable-memfd = yes
```

With this configuration, as each app started up, I noticed they were able to interact with audio
without issues. I also restarted my Bluetooth daemon and was able to pass audio through my BT-headset!



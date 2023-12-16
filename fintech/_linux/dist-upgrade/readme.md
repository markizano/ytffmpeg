# apt-get dist-upgrade

<!-- 0 -->
Hey guys, it's Markizano. If you're using Linux and you're on Devuan, you may have noticed they had
an upgrade recently. I'm a little late to the post here, but if you want to upgrade in-place without
a new install, here's how you do it.

Make sure to backup your systems before you begin. Always have backups, yeap.

Next, you're gonna update your package list here with `apt-get update` and `apt-get upgrade`.

This is going to install the latest packages and ensure that you are up to date with the latest patches
for the current version of your operating system. The last thing you want is for your system to be
trying to skip an update and trip over itself performing the update, and then your server ends up
in surgery. Let's not have apt-get surgery. It's very painful.

Next, you are going to disable your foreign package repositories by commenting all the files in
/etc/apt/sources.list.d. This will ensure no foreign software interferes with the upgrade process.
Again, we are trying to avoid that apt-get surgery, remember?

Once you have your repositories commented out, let's edit sources.list the main file and reduce it
down to the very main repository and change the destination from chimaera to daedalus.

Save the file and exit your text editor.

<!-- 92 -->
Now you are going to update your local repository cache with `apt-get update`. First, we need to 
install the latest dpkg and version of aptitude so `apt-get install dpkg apt` to install those. 
This was a pattern introduced to ensure the latest updates from the upstream are used for the 
upgrade whereas before you'd just upgrade from here. Once this is done, you'll have the latest 
versions of the Debian-based package managers.

<!-- 128 -->
You may see a prompt about news. It's a lesspipe so you can navigate with arrow keys, use the spacebar
for next page and "q" for leaving the message. Take note of what they have to say here though. Often
times developers are making updates and this is how you get to see what changes are coming in so
you can take action in your system accordingly.

<!-- 172 -->
As the system upgrades, it'll ask you about services to be restarted and files it needs to replace 
and if you want to change them or leave them. I forgot to include the options that mandate that 
aptitude leave the system as-is, so know there are ways of suppressing these messages. Just know 
that without the updates your system may need some manual tweaking to get it working with the 
latest software. So be on the lookout for any failed service restarts in this update.

<!-- 207 -->
When you finish with the upgrade you may get additional helpful information to know about your system.
For example, I was relieved to find out you have to set a kernel option now to enable net.ifnames
as depicted here as I was upset when they decided out of nowhere to change our network interface
names on us. #eth0 in the comments if you agree.

<!-- 260 -->
Now comes the part where it will take some time to upgrade the system.
For this part, I like to ensure that I am running in a screen session if I am SSH'd into a server,
because I've been disconnected mid-upgrade and let me tell you -- that is not sexy.

Now this time we are going to use `apt-get dist-upgrade`. This will do a deep inspection of your 
package listing and ensure all packages are upgraded to the latest version. It will also remove old 
and unused packages. Whereas apt-get upgrade might leave some things out and do a sloppy job.

Again, after downloading packages, it'll print the news. There's a few bullet points I wanted to
call out here:
- dhclient is stopping maintenance on the client part, so I will have to find a dhclient alternative.
- nfs-utils is no longer using /etc/default/* for config, instead use /etc/nfs.conf.d/local.conf.
- lots of updates in SSH, but basically we are getting better hashing algos and more secure configurations.
- You will no longer need to quote inner-glob scp results when targeting the remote? That's fantastic!
- The openssl upgrade breaks how openvpn works, so it will need a config update for encryption ciphers to work.
- fgrep and egrep are no longer a thing. Use their respective flags.

Once you've consumed all the updates, use "q" to exit from the lesspipe.
And we are off and running to the upgrade!
You may have to confirm your keyboard character set.
And the upgrade will tarry on quite nicely if all goes jolly!

This isn't actually how fast it goes, but you get the idea....

<!-- 1383 -->
After the upgrade is complete, I like to peek around at the new versions of software that I have
and make sure the package manager's packages are nice and tidy.
You can do this with `apt-get autoremove` and `apt-get autoclean`.
Autoremove will remove old packages that are obsolete, not in use or otherwise not necessary on your
system. Autoclean will delete the Debian packages downloaded to your local computer's cache.
You don't need those consuming your precious disk space!

<!-- 1576 -->
Once I see that no packages are left that need upgrading or cleaning, I will open up sources.list
to replace the other repositories for security updates and such.
Since we updated `sources.list`, we need to run `apt-get update` once more to update the package cache.

Now, we are going to run one more `apt-get dist-upgrade` to ensure security updates are installed
successfully and to completion. This may be a smaller list of packages that need an update and
more minimal changes to your system than before.

<!-- 1656 -->
Finally, I will go into sources.list.d and enable all the foreign package repositories from before
and edit them to ensure they are on compatible software for the version of Linux I am running.
You know the drill by now, we edited `sources.list`, so we will need to run one more `apt-get update`
to refresh the package list and the package manager knows where to find all the packages.
Then we can use `apt-get upgrade` to ensure those packages are up to date.

<!-- 1704 -->
But first: here's something tricky about aptitude that gets a lot of people since its a change in behaviour.
The GPG keys are no longer in a trusted.gpg keyring in the configuration. Instead, each package can
store their keys in /etc/apt/trusted.gpg.d/.

So you can run gpg --no-default-keyring --keyring /etc/apt/trusted.gpg -a --export "[KEY]" and pipe
that to a dedicated file in the trusted.gpg.d directory as depicted here. I have 3 keys to move
out of the keyring, so you'll see me do that now for MongoDB, NodeJS and Docker.

Once the keys have been exported from the keyring and into their own dedicated file, the subsequent
invocation of `apt-get update` should yield no warnings about keys in the keyring.

<!-- 1813 -->
Now you can `apt-get upgrade` or `apt-get install` the software you need to get to the latest version.

<!-- 1840 -->
With that, you're done with the update and it's time to reboot into your newly upgraded system!
I use `shutdown -F` to force check the filesystem on next boot to make sure everything is OK.






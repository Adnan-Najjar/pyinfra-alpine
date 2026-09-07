from pyinfra.operations import server, files, apk
from tasks.wireguard import wireguard_setup

# SSH hardening
files.put(
    name="Harden sshd configuration",
    src="files/sshd_config",
    dest="/etc/ssh/sshd_config.d/99-hardening.conf",
    mode="600",
)

# Non-root user
server.user(
    name="Non-root user",
    user="user",
    home="/home/user",
    shell="/bin/ash",
    groups=["wheel"],
    append=True,
    create_home=True,
)

# Firewall
apk.packages(
    name="Install firewall packages",
    packages=["nftables"],
)

server.shell(
    name="Configure firewall",
    commands=[
        # Chains & Rules
        "rc-update add nftables default",
    ],
)

# apk cache
files.directory(
    name="Create apk cache target directory",
    path="/var/cache/apk",
    present=True,
    _ignore_errors=True,
)

files.link(
    name="Configure apk cache symlink",
    path="/etc/apk/cache",
    target="/var/cache/apk",
    symbolic=True,
    force=True,
    _ignore_errors=True,
)

# Community repo
server.shell(
    name="Enable Alpine community repository",
    commands=[
        "sed -i 's|^#\\(.*\\/community\\)$|\\1|' /etc/apk/repositories",
    ],
)

# Update
apk.update()

# WireGuard setup
wireguard_setup(name="Setup WireGuard on inventory")

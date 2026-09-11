from pyinfra.context import host
from pyinfra.operations import server, files, apk
from pyinfra.facts.files import FindInFile
from tasks.wireguard import wireguard_setup

useradd_install = apk.packages(
    name="Install useradd from shadow package",
    packages=["shadow"],
)

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
    _if=useradd_install.did_succeed,
)

# Firewall
apk.packages(
    name="Install firewall packages",
    packages=["nftables"],
)
server.service(
    name="Enable firewall",
    service="nftables",
    enabled=True,
)

wg_rule = files.put(
    name="Configure firewall",
    src="files/wireguard.nft",
    dest="/etc/nftables.d/wireguard.nft",
    mode=644,
)
server.service(
    name="Restart firewall",
    service="nftables",
    restarted=True,
    _if=wg_rule.did_change
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
community_repo_links: list | None = host.get_fact(
    FindInFile,
    path="/etc/apk/repositories",
    pattern="^#.*community",
)

if community_repo_links:
    files.replace(
        name="Enable Alpine Community Repository",
        path="/etc/apk/repositories",
        text=community_repo_links[0],
        replace=community_repo_links[0].replace("#", ""),
    )

# Update
apk.update()

# WireGuard setup (wg_mesh hosts only)
if "wg_mesh" in host.groups:
    wireguard_setup(name="Setup WireGuard on wg_mesh")

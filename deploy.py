from pyinfra.context import host
from pyinfra.operations import files
from pyinfra.facts.files import FindInFile

from tasks.os_name import get_os_name
from tasks.users import user_setup
from tasks.firewall import firewall_setup
from tasks.wireguard import wireguard_setup

os_name = get_os_name()
is_alpine = os_name == "alpine"
is_freebsd = os_name == "freebsd"

# SSH hardening
files.put(
    name="Harden sshd configuration",
    src="files/sshd_config",
    dest="/etc/ssh/sshd_config.d/99-hardening.conf",
    mode="600",
)

# Non-root user
user_setup(name="Setup non-root user")

# Firewall
firewall_setup(name="Setup firewall")

if is_alpine:
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
    from pyinfra.operations import apk

    apk.update()

elif is_freebsd:
    # Update
    from pyinfra.operations.freebsd import pkg

    pkg.update()

# WireGuard setup (wg_mesh hosts only)
if "wg_mesh" in host.groups:
    wireguard_setup(name="Setup WireGuard on wg_mesh")

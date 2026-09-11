from pyinfra.context import host
from pyinfra.facts.server import Kernel, OsRelease


def get_os_name(host = host) -> str:
    kernel = host.get_fact(Kernel)
    if kernel == "FreeBSD":
        return "freebsd"
    os_release = host.get_fact(OsRelease) or {}
    return os_release.get("id") or kernel

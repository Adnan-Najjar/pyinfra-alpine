from pyinfra.context import host, inventory
from pyinfra.facts.server import Command
from pyinfra.facts.openrc import OpenrcStatus
from pyinfra.facts.files import File, FileContents
from pyinfra.api.operation import operation
from pyinfra.operations import files, server, apk


@operation()
def wireguard_setup(
    interface: str = "wg0",
    listen_port: int = 51820,
    private_key="/etc/wireguard/private.key",
    public_key="/etc/wireguard/public.key",
):

    # Install wireguard and create public and private keys (if they don't exist)
    if not host.get_fact(File, private_key):
        my_private_key = host.get_fact(
            Command,
            command=f"command -v wg >/dev/null 2>&1 || apk add -q wireguard-tools; "
            f"umask 077 &&"
            f"wg genkey | tee {private_key} | wg pubkey > {public_key}; "
            f"cat {private_key}",
        ).strip()
    else:
        my_private_key = host.get_fact(FileContents, private_key)

    # Build list of peers from all OTHER hosts in inventory
    peers = []
    for h in inventory:
        if h.name == host.name:
            continue

        # Get public key if it exists
        peer_pubkey = "".join(h.get_fact(FileContents, public_key)).strip()
        # If public key doesn't exist, but private key does, derive it from the private key
        if h.get_fact(File, private_key) and not peer_pubkey:
            peer_pubkey = h.get_fact(
                Command,
                command=f"command -v wg >/dev/null 2>&1 || apk add -q wireguard-tools; "
                f"umask 077 &&"
                f"wg pubkey < {private_key} > {public_key}; "
                f"cat {public_key}",
            ).strip()
        # If both doesn't exist, Create public and private keys (if they don't exist)
        elif not h.get_fact(File, private_key):
            peer_pubkey = h.get_fact(
                Command,
                command=f"command -v wg >/dev/null 2>&1 || apk add -q wireguard-tools; "
                f"umask 077 &&"
                f"wg genkey | tee {private_key} | wg pubkey > {public_key}; "
                f"cat {public_key}",
            ).strip()

        peer_wg_ip = h.data.get("wg_ip")
        # Skip if no WireGuard IP
        if not peer_wg_ip:
            continue

        peers.append(
            {
                "public_key": peer_pubkey,
                "allowed_ips": f"{peer_wg_ip.split('/')[0]}/32",  # Single IP address
                "endpoint": f"{h.name}:{listen_port}",
            }
        )

    yield from apk.packages._inner(
        packages=["wireguard-tools", "wireguard-tools-openrc"],
        update=True,
    )

    # Build configuration template (if it doesn't exist)
    if not host.get_fact(File, f"/etc/wireguard/{interface}.conf"):
        yield from files.template._inner(
            name="Build WireGuard config",
            src=f"templates/{interface}.conf.j2",
            dest=f"/etc/wireguard/{interface}.conf",
            mode="600",
            my_wg_ip=host.data.get("wg_ip"),
            my_private_key=my_private_key,
            listen_port=listen_port,
            peers=peers,
        )

    # Only create WireGuard service (if it doesn't exist)
    if not host.get_fact(File, f"/etc/init.d/wg-quick.{interface}"):
        yield from server.shell._inner(
            commands=[
                f"cp /etc/init.d/wg-quick /etc/init.d/wg-quick.{interface}",
            ],
        )

    # Start WireGuard (if it is not started)
    status = host.get_fact(OpenrcStatus)

    if status.get(f"wg-quick.{interface}") != "started":
        yield from server.service._inner(
            service=f"wg-quick.{interface}",
            enabled=True,
        )

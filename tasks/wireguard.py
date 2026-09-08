from pyinfra.context import host, inventory
from pyinfra.api.operation import operation
from pyinfra.operations import files, server
from pyinfra.facts.server import Command
from pyinfra.facts.files import File


@operation()
def wireguard_keygen():

    private_key: str = host.data.get("private_key") or "/etc/wireguard/private.key"
    public_key: str = host.data.get("public_key") or "/etc/wireguard/public.key"

    # Install wireguard
    yield from server.packages._inner(
        packages=["wireguard-tools", "wireguard-tools-openrc"]
    )

    # Create private key if it doesn't exist
    if not host.get_fact(File, private_key):
        yield from server.shell._inner(
            commands=[f"umask 077 && wg genkey > {private_key}"]
        )

    # Create public key if it doesn't exist
    if not host.get_fact(File, public_key):
        yield from server.shell._inner(
            commands=[f"wg pubkey < {private_key} > {public_key}"]
        )


@operation()
def wireguard_setup():

    interface: str = host.data.get("interface") or "wg0"
    listen_port: int = host.data.get("listen_port") or 51820
    private_key: str = host.data.get("private_key") or "/etc/wireguard/private.key"
    public_key: str = host.data.get("public_key") or "/etc/wireguard/public.key"

    my_private_key = host.get_fact(
        Command,
        command=f"cat {private_key}",
    )

    # Build list of peers from all OTHER hosts in inventory
    peers = []
    for h in inventory:
        if h.name == host.name or "wg_mesh" not in h.groups:
            continue

        # Get current host public key
        peer_pubkey = h.get_fact(
            Command,
            command=f"cat {public_key}",
        )
        # Skip if no public key
        if not peer_pubkey:
            continue

        # Skip if no WireGuard IP
        peer_wg_ip = h.data.get("wg_ip")
        if not peer_wg_ip:
            continue

        peers.append(
            {
                "public_key": peer_pubkey,
                "allowed_ips": f"{peer_wg_ip.split('/')[0]}/32",  # Single IP address
                "endpoint": f"{h.name}:{listen_port}",
            }
        )

    # Build configuration template
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

    # Create WireGuard service
    yield from files.put._inner(
        src="files/wg-quick",
        dest=f"/etc/init.d/wg-quick.{interface}",
        mode="755",
    )

    # Start WireGuard
    yield from server.service._inner(
        service=f"wg-quick.{interface}",
        running=True,
        enabled=True,
    )

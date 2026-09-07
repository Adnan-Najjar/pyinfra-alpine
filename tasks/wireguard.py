from pyinfra.context import host, inventory
from pyinfra.facts.openrc import OpenrcStatus
from pyinfra.facts.files import File
from pyinfra.api.operation import operation
from pyinfra.operations import files, server
from facts import WireGuardPrivateKey, WireGuardPublicKey


@operation()
def wireguard_setup():

    interface: str = host.data.get("interface") or "wg0"
    listen_port: int = host.data.get("listen_port") or 51820
    private_key: str = host.data.get("private_key") or "/etc/wireguard/private.key"
    public_key: str = host.data.get("public_key") or "/etc/wireguard/public.key"

    # Get current host private key (or create it if it doesn't exist)
    my_private_key = host.get_fact(WireGuardPrivateKey, private_key_path=private_key)

    # Build list of peers from all OTHER hosts in inventory
    peers = []
    for h in inventory:
        if h.name == host.name or "wg_mesh" not in h.groups:
            continue

        # Get current host public key (or create it if it doesn't exist)
        peer_pubkey = h.get_fact(
            WireGuardPublicKey,
            private_key_path=private_key,
            public_key_path=public_key,
        )
        if not peer_pubkey:
            h.get_fact(
                WireGuardPrivateKey,
                private_key_path=private_key,
            )
            peer_pubkey = h.get_fact(
                WireGuardPublicKey,
                private_key_path=private_key,
                public_key_path=public_key,
            )
            if not peer_pubkey:
                continue

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

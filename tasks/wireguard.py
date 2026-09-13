from pathlib import Path
from pyinfra.context import host, inventory
from pyinfra.api.command import StringCommand
from pyinfra.api.operation import operation
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server
from pyinfra.facts.files import File, FileContents

from tasks.os_name import get_os_name


@operation()
def wireguard_keygen(private_key_path: str, public_key_path: str):

    os_name = get_os_name()

    # Install wireguard
    if os_name == "alpine":
        yield from server.packages._inner(
            packages=["wireguard-tools", "wireguard-tools-openrc"],
        )
    elif os_name == "freebsd":
        from pyinfra.operations.freebsd import pkg

        yield from pkg.install._inner(package="wireguard-tools")

    # Create private key if it doesn't exist
    if not host.get_fact(File, path=private_key_path):
        yield StringCommand(f"umask 077 && wg genkey > {private_key_path}")

    # Create public key if it doesn't exist
    if not host.get_fact(File, path=public_key_path):
        yield StringCommand(f"wg pubkey < {private_key_path} > {public_key_path}")


@deploy("WireGuard setup")
def wireguard_setup():

    os_name = get_os_name()

    interface: str = host.data.get("wg_interface") or "wg0"
    listen_port: int = host.data.get("wg_listen_port") or 51820
    private_key: str = host.data.get("private_key") or "/etc/wireguard/private.key"
    public_key: str = host.data.get("public_key") or "/etc/wireguard/public.key"

    if os_name == "freebsd":
        private_key = "/usr/local/etc/wireguard/private.key"
        public_key = "/usr/local/etc/wireguard/public.key"

    config_path = str(Path(private_key).parent)

    # Generate WireGuard keys
    wireguard_keygen(
        name="Generate keys for WireGuard",
        private_key_path=private_key,
        public_key_path=public_key,
    )

    my_private_key = host.get_fact(FileContents, private_key)
    if my_private_key:
        my_private_key = my_private_key[0].strip()

    # Build list of peers from all OTHER hosts in inventory
    peers = []
    for h in inventory:
        if h.name == host.name or "wg_mesh" not in h.groups:
            continue

        # Get current host public key
        if get_os_name(h) == "freebsd":
            private_key = "/usr/local/etc/wireguard/private.key"
            public_key = "/usr/local/etc/wireguard/public.key"
        else:
            private_key = h.data.get("private_key") or "/etc/wireguard/private.key"
            public_key = h.data.get("public_key") or "/etc/wireguard/public.key"
        peer_pubkey = h.get_fact(FileContents, public_key)
        if peer_pubkey and peer_pubkey[0].strip():
            peer_pubkey = peer_pubkey[0].strip()
        # Skip if no public key
        else:
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
    wg_config = files.template(
        name="Build WireGuard config",
        src=f"templates/{interface}.conf.j2",
        dest=f"{config_path}/{interface}.conf",
        mode="600",
        my_wg_ip=host.data.get("wg_ip"),
        my_private_key=my_private_key,
        listen_port=listen_port,
        peers=peers,
    )

    if os_name == "alpine":
        files.put(
            name="Create WireGuard service",
            src="files/wg-quick-openrc",
            dest=f"/etc/init.d/wg-quick.{interface}",
            mode="755",
        )

        server.service(
            name="Start WireGuard service",
            service=f"wg-quick.{interface}",
            running=True,
            enabled=True,
        )

        server.shell(
            name="Reload WireGuard config",
            commands=[
                f"wg-quick strip {config_path}/{interface}.conf | wg syncconf {interface} /dev/stdin",
            ],
            _if=wg_config.did_change,
        )

    elif os_name == "freebsd":
        from pyinfra.operations.freebsd import sysrc, service

        sysrc.sysrc(
            name="Load WireGuard kernel module",
            parameter="kldload",
            value="if_wg",
            command="add",
        )

        sysrc.sysrc(
            name="Set WireGuard interface",
            parameter="wireguard_interfaces",
            value=interface,
        )

        sysrc.sysrc(
            name="Enable WireGuard",
            parameter="wireguard_enable",
            value="YES",
        )

        service.service(
            name="Start WireGuard service",
            srvname=f"wireguard",
            srvstate="started",
            _if=wg_config.did_change,
        )

        server.shell(
            name="Reload WireGuard config",
            commands=[
                f"wg-quick strip {config_path}/{interface}.conf | wg syncconf {interface} /dev/stdin",
            ],
            _if=wg_config.did_change,
        )

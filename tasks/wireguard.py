from pyinfra.context import host, inventory
from pyinfra.facts.server import Command
from pyinfra.operations import files, server, apk

private_key = "/etc/wireguard/private.key"
public_key = "/etc/wireguard/public.key"
wg_listen_port = host.data.get("wg_listen_port", 51820)
my_wg_ip = host.data.get("wg_ip")

# Install wireguard and create public and private keys (if they don't exist)
my_private_key = host.get_fact(
    Command,
    command=f"command -v wg >/dev/null 2>&1 || apk add -q wireguard-tools; "
    f"umask 077 && [ -f {private_key} ] || "
    f"wg genkey | tee {private_key} | wg pubkey > {public_key}; "
    f"cat {private_key}",
).strip()

# Build list of peers from all OTHER hosts in inventory
peers = []
for h in inventory:
    if h.name == host.name:
        continue

    # Install wireguard and create public and private keys (if they don't exist)
    peer_pubkey = h.get_fact(
        Command,
        command=f"command -v wg >/dev/null 2>&1 || apk add -q wireguard-tools; "
        f"umask 077 && [ -f {private_key} ] || "
        f"wg genkey | tee {private_key} | wg pubkey > {public_key}; "
        f"cat {public_key}",
    )

    peer_ip = h.data.get("wg_ip")
    if not peer_ip:
        continue
    peer_port = h.data.get("wg_listen_port", 51820)

    peers.append(
        {
            "public_key": peer_pubkey,
            "allowed_ips": f"{peer_ip.split('/')[0]}/32",  # Single IP address
            "endpoint": f"{h.name}:{peer_port}",
        }
    )

apk.packages(
    name="Install WireGuard tools",
    packages=["wireguard-tools", "wireguard-tools-openrc"],
)

# Build configuration template
files.template(
    name="Build WireGuard config",
    src="templates/wg0.conf.j2",
    dest="/etc/wireguard/wg0.conf",
    mode="600",
    my_wg_ip=my_wg_ip,
    my_private_key=my_private_key,
    listen_port=wg_listen_port,
    peers=peers,
)

files.link(
    name="Create a WireGuard service",
    path="/etc/init.d/wg-quick.wg0",
    target="/etc/init.d/wg-quick",
)

server.service(
    name="Start WireGuard rc service",
    service="wg-quick.wg0",
    reloaded=True,
    enabled=True,
)

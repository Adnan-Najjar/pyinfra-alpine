from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

from tasks.os_name import get_os_name


@deploy("Firewall setup")
def firewall_setup():
    os_name = get_os_name()

    is_wireguard = "wg_mesh" in host.groups
    wg_interface = host.data.get("wg_interface")
    wg_port = host.data.get("wg_listen_port")
    is_http = host.data.get("web_server")

    if os_name == "alpine":
        from pyinfra.operations import apk

        apk.packages(
            name="Install firewall packages",
            packages=["nftables"],
        )
        server.service(
            name="Enable firewall (nftables)",
            service="nftables",
            enabled=True,
        )

        nftable_rules = files.template(
            name="Configure firewall (nftables)",
            src="templates/nftables.nft.j2",
            dest="/etc/nftables.d/default.nft",
            mode=644,
            wireguard=is_wireguard,
            wg_interface=wg_interface,
            wg_port=wg_port,
            http=is_http,
        )

        server.service(
            name="Restart firewall (nftables)",
            service="nftables",
            restarted=True,
            _if=nftable_rules.did_change,
        )

    elif os_name == "freebsd":
        from pyinfra.operations.freebsd import service, sysrc

        sysrc.sysrc(
            name="Enable Packet Filter (pf)",
            parameter="pf_enable",
            value="YES",
        )

        pf_conf = files.template(
            name="Configure firewall (pf)",
            src="templates/pf.conf.j2",
            dest="/etc/pf.conf",
            mode=600,
            wireguard=is_wireguard,
            wg_interface=wg_interface,
            wg_port=wg_port,
            http=is_http,
        )

        server.shell(
            name="Enable and Load pf rules",
            commands=["pfctl -f /etc/pf.conf"],
            _if=pf_conf.did_change,
        )

        service.service(
            srvname="pf",
            srvstate="started",
        )

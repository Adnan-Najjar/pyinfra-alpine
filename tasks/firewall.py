from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

from tasks.os_name import get_os_name


@deploy("Firewall setup")
def firewall_setup():
    os_name = get_os_name()

    if os_name == "alpine":
        from pyinfra.operations import apk

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
            _if=wg_rule.did_change,
        )

    elif os_name == "freebsd":
        from pyinfra.operations.freebsd import service, sysrc

        sysrc.sysrc(
            name="Enable Packet Filter (pf)",
            parameter="pf_enable",
            value="YES",
        )
        wg_rule = files.put(
            name="Configure firewall (pf)",
            src="files/pf.conf",
            dest="/etc/pf.conf",
            mode=600,
        )

        server.shell(
            name="Enable and Load pf rules",
            commands=["pfctl -ef /etc/pf.conf"],
            _if=wg_rule.did_change,
        )

        service.service(
            srvname="pf",
            srvstate="started",
        )

from typing import override, Any
from pyinfra.api.facts import FactBase
from pyinfra.facts.server import Command, Which
from pyinfra.api.host import Host
from pyinfra.api.state import State


class WireGuardPrivateKey(FactBase[str | None]):
    @override
    def requires_command(self, *args: Any, **kwargs: Any) -> str:
        return "wg"

    @override
    def check_preconditions(
        self,
        _state: State,
        host: Host,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Make sure wireguard is installed
        if not host.get_fact(Which, command="wg"):
            host.get_fact(
                Command,
                command="apk update && apk add wireguard-tools wireguard-tools-openrc",
            )

    @override
    def command(
        self,
        private_key_path: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        return (
            f"! test -f {private_key_path} && "
            f"umask 077 && wg genkey | tee {private_key_path} || true"
        )

    @override
    def process(self, output: list[str]) -> str | None:
        if output and output[0].strip():
            return output[0].strip()
        return None


class WireGuardPublicKey(FactBase[str | None]):
    @override
    def requires_command(self, *args: Any, **kwargs: Any) -> str:
        return "wg"

    @override
    def check_preconditions(
        self,
        _state: State,
        host: Host,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Make sure wireguard is installed
        if not host.get_fact(Which, command="wg"):
            host.get_fact(
                Command,
                command="apk update && apk add wireguard-tools wireguard-tools-openrc",
            )

    @override
    def command(
        self,
        private_key_path: str,
        public_key_path: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        return (
            f"test -f {private_key_path} && "
            f"umask 077 && wg pubkey < {private_key_path} | tee {public_key_path} || true"
        )

    @override
    def process(self, output: list[str]) -> str | None:
        if output and output[0].strip():
            return output[0].strip()
        return None

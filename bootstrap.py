from pyinfra.operations import server
from pathlib import Path

SSH_KEY = Path("~/.ssh/id_ed25519.pub").expanduser().read_text().strip()

server.user(
    name="Create admin user",
    user="admin",
    home="/home/admin",
    shell="/bin/ash",
    groups=["wheel"],
    append=True,
    create_home=True,
    public_keys=[SSH_KEY],
)

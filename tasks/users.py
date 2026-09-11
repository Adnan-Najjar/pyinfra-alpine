from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import server
from pyinfra.facts.server import Users

from tasks.os_name import get_os_name


@deploy("User setup")
def user_setup(username: str = "user"):
    os_name = get_os_name()

    if os_name == "alpine":
        from pyinfra.operations import apk

        useradd_install = apk.packages(
            name="Install useradd from shadow package",
            packages=["shadow"],
        )
        server.user(
            name=f"Non-root user ({username})",
            user=username,
            home=f"/home/{username}",
            shell="/bin/ash",
            groups=["wheel"],
            append=True,
            create_home=True,
            _if=useradd_install.did_succeed,
        )

    elif os_name == "freebsd":
        users = host.get_fact(Users)
        if username not in users:
            server.shell(
                name=f"Create non-root user ({username})",
                commands=[
                    f"pw useradd {username} -m -G wheel -s /bin/csh -d /home/{username}"
                ],
            )

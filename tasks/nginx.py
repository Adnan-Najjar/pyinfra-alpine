from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server

from tasks.os_name import get_os_name


@deploy("nginx web server setup")
def nginx_setup():
    os_name = get_os_name()

    if os_name == "alpine":
        from pyinfra.operations import apk

        apk.packages(
            name="Install nginx",
            packages=["nginx"],
        )
        server.service(
            name="Enable nginx",
            service="nginx",
            enabled=True,
        )

        conf = files.put(
            name="Configure nginx site",
            src="files/nginx-default.conf",
            dest="/etc/nginx/http.d/default.conf",
            mode=644,
        )
        server.service(
            name="Restart nginx",
            service="nginx",
            restarted=True,
            _if=conf.did_change,
        )
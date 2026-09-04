wg_listen_port = 51820

hosts = [
    (
        "10.16.251.9",
        {
            "wg_ip": "192.168.2.1/24",
            "ssh_user": "root",
            "ssh_key": "~/.ssh/lab_key",
        },
    ),
    (
        "10.16.251.201",
        {
            "wg_ip": "192.168.2.2/24",
            "ssh_user": "root",
            "ssh_key": "~/.ssh/lab_key",
        },
    ),
    (
        "10.16.251.29",
        {
            "wg_ip": "192.168.2.3/24",
            "ssh_user": "root",
            "ssh_key": "~/.ssh/lab_key",
        },
    ),
]

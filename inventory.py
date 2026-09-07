wg_listen_port = 51820

hosts = [
    (
        "@incus/vm1",
        {"wg_ip": "192.168.2.1/24"},
    ),
    (
        "@incus/vm2",
        {"wg_ip": "192.168.2.2/24"},
    ),
    (
        "@incus/vm3",
        {"wg_ip": "192.168.2.3/24"},
    ),
]

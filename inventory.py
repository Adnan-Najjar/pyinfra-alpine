hosts = [
    "@incus/vm4",
]

wg_mesh = [
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

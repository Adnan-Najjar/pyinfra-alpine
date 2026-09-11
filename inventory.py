hosts = [
    "@incus/vm4",
]

wg_mesh = [
    (
        "@incus/vm1",
        {
            "wg_ip": "192.168.2.1/24",
            "endpoint": "",
        },
    ),
    (
        "@incus/vm2",
        {
            "wg_ip": "192.168.2.2/24",
            "endpoint": "",
        },
    ),
    (
        "@incus/vm3",
        {
            "wg_ip": "192.168.2.3/24",
            "endpoint": "",
        },
    ),
    (
        "@incus/freebsd",
        {
            "wg_ip": "192.168.2.4/24",
        },
    ),
]

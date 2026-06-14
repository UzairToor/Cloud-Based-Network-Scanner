import ipaddress
from typing import List


def validate_ip_range(ip_range: str) -> bool:
    try:
        ipaddress.IPv4Network(ip_range, strict=False)
        return True
    except ValueError:
        return False


def validate_gateway(ip_range: str, gateway: str) -> bool:
    if not gateway:
        return True

    try:
        network = ipaddress.ip_network(ip_range, strict=False)
        gw_ip = ipaddress.ip_address(gateway)
        return gw_ip in network
    except ValueError:
        return False


def validate_port_list(ports: List[int]) -> bool:
    if not ports:
        return False

    for port in ports:
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return False

    return True

import os
from typing import List, Dict

from scapy.all import ARP, Ether, srp  # type: ignore


def scan_network(ip_range: str) -> List[Dict[str, str]]:
    """
    Scan the specified IP range for active devices using ARP requests.

    NOTE:
    - ARP scanning requires admin/root privileges.
    - ARP scanning is disabled in cloud environments (e.g., Render).

    Args:
        ip_range (str): IP range in CIDR format (e.g., "192.168.1.1/24")

    Returns:
        List[Dict[str, str]]: List of discovered devices with IP and MAC.
    """

    # Disable ARP scanning in cloud environments
    if os.getenv("RENDER") == "true":
        return []

    # Build ARP request packet
    arp_request = ARP(pdst=ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request

    try:
        answered_list = srp(packet, timeout=2, verbose=False)[0]
    except PermissionError as exc:
        raise PermissionError(
            "ARP scanning requires administrative/root privileges."
        ) from exc

    devices: List[Dict[str, str]] = []

    for _, received in answered_list:
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc
        })

    return devices

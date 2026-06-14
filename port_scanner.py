import socket
from typing import List

def scan_ports(host: str, ports: List[int], timeout: int = 1) -> List[int]:
    """
    Scans a list of ports on a given host to identify open ports.

    Args:
        host (str): Target host IP address.
        ports (List[int]): List of port numbers to scan.
        timeout (int): Socket timeout in seconds.

    Returns:
        List[int]: List of open ports.
    """

    open_ports: List[int] = []

    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                if sock.connect_ex((host, port)) == 0:
                    open_ports.append(port)

        except socket.timeout:
            # Port filtered or unresponsive – ignore safely
            continue

        except OSError:
            # Host unreachable or invalid socket state
            continue

    return open_ports
